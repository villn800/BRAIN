from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable, List, Sequence
from uuid import UUID
from urllib.parse import urlparse

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import storage

PATH_FIELDS = ("file_path", "thumbnail_path")
logger = logging.getLogger(__name__)


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
    tag_names: Iterable[str] | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
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
    tag_filters: List[str] = []
    if tag_name:
        tag_filters.append(tag_name)
    if tag_names:
        if isinstance(tag_names, str):
            tag_filters.append(tag_names)
        else:
            tag_filters.extend(tag_names)
    normalized_tags = _normalize_tag_filters(tag_filters)
    if normalized_tags:
        # Require every requested tag by grouping on item and enforcing the count of
        # distinct tag names. This keeps multi-tag queries deterministic for the UI.
        matched_items = (
            db.query(models.Item.id)
            .join(models.Item.tags)
            .filter(
                models.Item.user_id == user.id,
                func.lower(models.Tag.name).in_(normalized_tags),
            )
            .group_by(models.Item.id)
            .having(
                func.count(func.distinct(func.lower(models.Tag.name)))
                >= len(normalized_tags)
            )
        )
        query = query.filter(models.Item.id.in_(matched_items))
    if created_from:
        query = query.filter(models.Item.created_at >= created_from)
    if created_to:
        query = query.filter(models.Item.created_at <= created_to)
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
    paths = _collect_paths(item)
    db.delete(item)
    db.commit()
    for path in paths:
        storage.safe_remove_path(path)


def delete_item_and_assets(
    db: Session,
    user: models.User,
    item_id: UUID,
) -> bool:
    item = get_item(db, user, item_id)
    if not item:
        return False
    delete_item(db, item)
    logger.info("Deleted item and assets", extra={"user_id": str(user.id), "item_id": str(item.id)})
    return True


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


def _normalize_tag_filters(values: Iterable[str]) -> List[str]:
    normalized: List[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        cleaned = value.strip().lower()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _collect_paths(item: models.Item) -> List[str]:
    paths: List[str] = []
    for field in PATH_FIELDS:
        value = getattr(item, field, None)
        if value:
            paths.append(value)
    return paths
