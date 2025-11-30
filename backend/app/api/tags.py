from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core.security import get_current_user
from ..database import get_db
from ..services import tags_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=List[schemas.TagSummary])
def list_tags(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    summaries = []
    for tag, item_count in tags_service.list_tags(db, current_user):
        summaries.append(
            schemas.TagSummary(
                id=tag.id,
                name=tag.name,
                item_count=item_count,
            )
        )
    return summaries


@router.post("/", response_model=schemas.TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        tag = tags_service.create_tag(db, current_user, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        tags_service.delete_tag(db, current_user, tag_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc