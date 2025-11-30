from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core.security import get_current_user
from ..database import get_db
from ..services import items_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=List[schemas.ItemOut])
def list_items(
    q: str | None = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return items_service.list_items(
        db,
        current_user,
        search=q,
        limit=limit,
        offset=offset,
    )
