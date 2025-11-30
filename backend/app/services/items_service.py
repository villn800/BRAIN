from __future__ import annotations

from typing import Iterable, List, Sequence
from uuid import UUID
from urllib.parse import urlparse

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import storage

PATH_FIELDS = ("file_path", "thumbnail_path")


def _derive_origin_domain(source_url: str | None) -> str | None:
    if not source_url:
        return None
    parsed = urlparse(str(source_url))
    if not parsed.netloc:
        return None
    return parsed.netloc.lower()


def _normalize_domain(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def _apply_common_normalization(data: dict[str, object]) -> None:
    if "source_url" in data and data["source_url"] is not None:
        data["source_url"] = str(data["source_url"])

    if "origin_domain" in data:
        data["origin_domain"] = _normalize_domain(data["origin_domain"])  # type: ignore[arg-type]
    elif data.get("source_url"):
        data["origin_domain"] = _derive_origin_domain(data.get("source_url"))

    for field in PATH_FIELDS:
        if field in data:
            normalized = storage.normalize_relative_path(data[field])  # type: ignore[arg-type]
            data[field] = normalized

    if "original_filename" in data and data["original_filename"]:
        original = str(data["original_filename"]).strip()
        data["original_filename"] = original or None

    if "content_type" in data and data["content_type"]:
        content_type = str(data["content_type"]).strip()
        data["content_type"] = content_type or None


def list_items(
    db: Session,
    user: models.User,
    *,
    search: str | None = None,
    item_type: models.ItemType | None = None,
    status: models.ItemStatus | None = None,
    origin_domain: str | None = None,
    tag_name: str | None = None,
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
    if item_type:
        query = query.filter(models.Item.type == item_type)
    if status:
        query = query.filter(models.Item.status == status)
    if origin_domain:
        query = query.filter(models.Item.origin_domain == origin_domain.strip().lower())
    if tag_name:
        query = query.join(models.Item.tags).filter(
            func.lower(models.Tag.name) == tag_name.strip().lower()
        )
        query = query.distinct()
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
    data = payload.model_dump(exclude_none=True)
    _apply_common_normalization(data)
    item = models.Item(user_id=user.id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session,
    item: models.Item,
    payload: schemas.ItemUpdate,
) -> models.Item:
    updates = payload.model_dump(exclude_unset=True)
    _apply_common_normalization(updates)
    for key, value in updates.items():
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

