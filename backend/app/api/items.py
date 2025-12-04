import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import storage
from ..core.security import get_current_user
from ..database import get_db
from ..services import file_processing, ingestion_service, items_service

router = APIRouter(prefix="/items", tags=["items"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[schemas.ItemOut])
def list_items(
    q: str | None = Query(None, description="Case-insensitive keyword search across title, description, and extracted text"),
    item_type: models.ItemType | None = Query(None, alias="type", description="Restrict results to a specific item type"),
    status_filter: models.ItemStatus | None = Query(None, alias="status", description="Filter by ingestion or processing status"),
    origin_domain: str | None = Query(None, description="Filter by normalized source domain (e.g., pinterest.com)"),
    tag: str | None = Query(None, description="Filter by a single tag name"),
    tags: List[str] | None = Query(None, description="Require items to contain **all** of the provided tags (intersection semantics)"),
    created_from: datetime | None = Query(None, description="ISO-8601 timestamp; include items created at or after this moment"),
    created_to: datetime | None = Query(None, description="ISO-8601 timestamp; include items created at or before this moment"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="How many newest items to skip before returning results"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the authenticated user's items ordered newest-first with flexible search and filter controls."""
    return items_service.list_items(
        db,
        current_user,
        search=q,
        item_type=item_type,
        status=status_filter,
        origin_domain=origin_domain,
        tag_name=tag,
        tag_names=tags,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )


@router.post("/url", response_model=schemas.ItemOut, status_code=status.HTTP_201_CREATED)
def create_item_from_url(
    payload: schemas.UrlIngestionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = ingestion_service.ingest_url(db, current_user, payload)
    logger.info(
        "URL item created",
        extra={"user_id": str(current_user.id), "item_id": str(item.id)},
    )
    return item


@router.post("/upload", response_model=schemas.ItemOut, status_code=status.HTTP_201_CREATED)
def upload_item(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    description: str | None = Form(default=None),
    tags: List[str] | None = Form(default=None),
    tags_csv: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tag_values = list(tags or [])
    if tags_csv:
        tag_values.extend(
            tag.strip()
            for tag in tags_csv.split(",")
            if tag.strip()
        )

    media_kind = None
    if file_processing.detect_image_media(file):
        media_kind = "image"
    elif file_processing.detect_pdf_media(file):
        media_kind = "pdf"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    try:
        with storage.FileWriteGuard() as guard:
            if media_kind == "image":
                result = file_processing.process_image_upload(file, guard=guard)
            else:
                result = file_processing.process_pdf_upload(file, guard=guard)

            item_payload = schemas.ItemCreate(
                title=_derive_upload_title(title, file, result),
                description=description,
                type=result.item_type,
                status=result.status,
                file_path=result.file_path,
                thumbnail_path=result.thumbnail_path,
                text_content=result.text_content,
                original_filename=result.original_filename,
                content_type=result.content_type,
                file_size_bytes=result.file_size_bytes,
            )
            item = items_service.create_item(db, current_user, item_payload)
    except file_processing.UploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except file_processing.UploadProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if tag_values:
        item = items_service.set_item_tags(db, current_user, item, tag_values)
    logger.info(
        "File uploaded",
        extra={
            "user_id": str(current_user.id),
            "item_id": str(item.id),
            "media_kind": media_kind,
        },
    )
    return item


@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = items_service.get_item(db, current_user, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("/", response_model=schemas.ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: schemas.ItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return items_service.create_item(db, current_user, payload)


@router.patch("/{item_id}", response_model=schemas.ItemOut)
def update_item(
    item_id: UUID,
    payload: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = items_service.get_item(db, current_user, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return items_service.update_item(db, item, payload)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    deleted = items_service.delete_item_and_assets(db, current_user, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    logger.info(
        "Item deleted",
        extra={"user_id": str(current_user.id), "item_id": str(item_id)},
    )


@router.put("/{item_id}/tags", response_model=schemas.ItemOut)
def replace_item_tags(
    item_id: UUID,
    payload: schemas.ItemTagsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = items_service.get_item(db, current_user, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    updated = items_service.set_item_tags(db, current_user, item, payload.tags)
    logger.info(
        "Item tags updated",
        extra={"user_id": str(current_user.id), "item_id": str(item.id), "tag_count": len(payload.tags)},
    )
    return updated


@router.get("/{item_id}/tags", response_model=List[schemas.TagOut])
def list_item_tags(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    item = items_service.get_item(db, current_user, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item.tags


def _derive_upload_title(
    provided: str | None,
    upload: UploadFile,
    result: file_processing.FileProcessingResult,
) -> str:
    if provided:
        stripped = provided.strip()
        if stripped:
            return stripped
    if upload.filename:
        candidate = upload.filename.strip()
        if candidate:
            return candidate
    item_label = result.item_type.value.capitalize()
    return f"Uploaded {item_label}"
