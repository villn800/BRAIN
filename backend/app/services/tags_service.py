from __future__ import annotations

from typing import List, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models


def list_tags(db: Session, user: models.User) -> List[Tuple[models.Tag, int]]:
    results = (
        db.query(models.Tag, func.count(models.ItemTag.item_id))
        .outerjoin(models.ItemTag, models.ItemTag.tag_id == models.Tag.id)
        .filter(models.Tag.user_id == user.id)
        .group_by(models.Tag.id)
        .order_by(func.lower(models.Tag.name))
        .all()
    )
    return [(tag, item_count) for tag, item_count in results]


def create_tag(db: Session, user: models.User, name: str) -> models.Tag:
    cleaned = (name or "").strip()
    if not cleaned:
        raise ValueError("Tag name is required")
    existing = (
        db.query(models.Tag)
        .filter(models.Tag.user_id == user.id, func.lower(models.Tag.name) == cleaned.lower())
        .first()
    )
    if existing:
        raise ValueError("Tag already exists")
    tag = models.Tag(user_id=user.id, name=cleaned)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, user: models.User, tag_id: UUID) -> None:
    tag = (
        db.query(models.Tag)
        .filter(models.Tag.user_id == user.id, models.Tag.id == tag_id)
        .first()
    )
    if not tag:
        raise LookupError("Tag not found")
    db.delete(tag)
    db.commit()