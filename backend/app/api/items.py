from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core.security import get_current_user
from ..database import get_db
from ..services import ingestion_service, items_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=List[schemas.ItemOut])
def list_items(
    q: str | None = Query(None, description="Search query"),
    item_type: models.ItemType | None = Query(None, alias="type"),
    status_filter: models.ItemStatus | None = Query(None, alias="status"),
    origin_domain: str | None = Query(None, description="Filter by normalized domain"),
    tag: str | None = Query(None, description="Filter by tag name"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return items_service.list_items(
        db,
        current_user,
        search=q,
        item_type=item_type,
        status=status_filter,
        origin_domain=origin_domain,
        tag_name=tag,
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
    item = items_service.get_item(db, current_user, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    items_service.delete_item(db, item)


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
    return items_service.set_item_tags(db, current_user, item, payload.tags)
