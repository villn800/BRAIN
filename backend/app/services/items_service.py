from __future__ import annotations

from typing import Iterable, List, Sequence
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas


def list_items(
    db: Session,
    user: models.User,
    *,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[models.Item]:
    query = db.query(models.Item).filter(models.Item.user_id == user.id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.Item.title.ilike(like),
                models.Item.description.ilike(like),
                models.Item.text_content.ilike(like),
            )
        )
    return (
        query.order_by(models.Item.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_item(
    db: Session,
    user: models.User,
    item_id: UUID,
) -> models.Item | None:
    return (
        db.query(models.Item)
        .filter(models.Item.user_id == user.id, models.Item.id == item_id)
        .first()
    )


def create_item(
    db: Session,
    user: models.User,
    payload: schemas.ItemCreate,
) -> models.Item:
    item = models.Item(user_id=user.id, **payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session,
    item: models.Item,
    payload: schemas.ItemUpdate,
) -> models.Item:
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: models.Item) -> None:
    db.delete(item)
    db.commit()


def set_item_tags(
    db: Session,
    user: models.User,
    item: models.Item,
    tag_names: Iterable[str],
) -> models.Item:
    unique_names: dict[str, str] = {}
    for name in tag_names:
        if not name:
            continue
        cleaned = name.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        unique_names.setdefault(key, cleaned)

    tags: List[models.Tag] = []
    for key, display_name in unique_names.items():
        tag = (
            db.query(models.Tag)
            .filter(
                models.Tag.user_id == user.id,
                func.lower(models.Tag.name) == key,
            )
            .first()
        )
        if not tag:
            tag = models.Tag(user_id=user.id, name=display_name)
            db.add(tag)
            db.flush()
        tags.append(tag)

    item.tags = tags
    db.commit()
    db.refresh(item)
    return item

