from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from typing import Mapping

import httpx
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import storage, urls
from . import items_service, metadata_service, url_extractors
from .time_utils import parse_metadata_timestamp, parse_twitter_timestamp_from_url

logger = logging.getLogger(__name__)

IMAGE_TIMEOUT = 15.0


def ingest_url(
    db: Session,
    user: models.User,
    payload: schemas.UrlIngestionRequest,
    *,
    http_get: metadata_service.HttpGetter | None = None,
    image_get: metadata_service.HttpGetter | None = None,
) -> models.Item:
    normalized = urls.normalize_url(payload.url)
    html_result = metadata_service.fetch_html(
        normalized.url,
        http_get=http_get,
    )

    metadata = url_extractors.extract_for_domain(
        normalized.domain,
        normalized.url,
        html_result.html,
    )
    if metadata is None:
        metadata = metadata_service.parse_generic_metadata(normalized.url, html_result.html)

    metadata.error = metadata.error or html_result.error

    status = models.ItemStatus.ok
    if html_result.error and not html_result.html:
        status = models.ItemStatus.failed

    final_title = payload.title or metadata.title or normalized.url
    file_path: str | None = None
    image_error: str | None = None
    if metadata.image_url and url_extractors._looks_like_image_url(metadata.image_url):
        file_path, image_error = _download_primary_image(
            metadata.image_url,
            image_get=image_get,
        )
        if image_error:
            logger.warning("Failed to download image for %s: %s", normalized.url, image_error)
            if status == models.ItemStatus.ok:
                status = models.ItemStatus.pending

    created_at = parse_metadata_timestamp((metadata.extra or {}).get("timestamp"))
    if not created_at and metadata.item_type == models.ItemType.tweet:
        created_at = parse_twitter_timestamp_from_url(normalized.url)

    item_payload = schemas.ItemCreate(
        title=final_title,
        description=metadata.description,
        type=metadata.item_type or models.ItemType.url,
        status=status,
        source_url=normalized.url,
        origin_domain=normalized.domain,
        file_path=file_path,
        extra=metadata.extra or None,
    )

    item = items_service.create_item(db, user, item_payload, created_at=created_at)

    if payload.tags:
        items_service.set_item_tags(db, user, item, payload.tags)

    return item


def refresh_url_item(
    db: Session,
    user: models.User,
    item: models.Item,
    *,
    force_download: bool = False,
    update_text: bool = False,
    http_get: metadata_service.HttpGetter | None = None,
    image_get: metadata_service.HttpGetter | None = None,
    commit: bool = True,
) -> models.Item:
    if item.user_id != user.id:
        raise ValueError("Cannot refresh an item you do not own")
    if not item.source_url:
        raise ValueError("Cannot refresh item without source_url")

    normalized = urls.normalize_url(item.source_url)
    html_result = metadata_service.fetch_html(
        normalized.url,
        http_get=http_get,
    )

    metadata = url_extractors.extract_for_domain(
        normalized.domain,
        normalized.url,
        html_result.html,
    )
    if metadata is None:
        metadata = metadata_service.parse_generic_metadata(normalized.url, html_result.html)

    needs_twitter_fallback = bool(
        html_result.error
        or not html_result.html
        or not url_extractors._looks_like_image_url(metadata.image_url)
    )
    if needs_twitter_fallback:
        _maybe_apply_twitter_fallback(normalized.domain, normalized.url, metadata)

    metadata.error = metadata.error or html_result.error
    status = models.ItemStatus.ok
    metadata_present = bool(
        (metadata.title and metadata.title.strip())
        or (metadata.description and metadata.description.strip())
        or metadata.image_url
        or metadata.extra
    )
    if html_result.error and not html_result.html and not metadata_present:
        status = models.ItemStatus.failed

    should_download = False
    existing_extra = item.extra or {}
    if metadata.image_url and url_extractors._looks_like_image_url(metadata.image_url):
        should_download = (
            force_download
            or not item.file_path
            or bool(existing_extra.get("primary_image_is_avatar"))
        )

    file_path = item.file_path
    thumbnail_path = item.thumbnail_path
    image_error: str | None = None
    if should_download:
        downloaded_path, image_error = _download_primary_image(
            metadata.image_url,  # type: ignore[arg-type]
            image_get=image_get,
        )
        if image_error:
            logger.warning("Failed to download image for %s: %s", normalized.url, image_error)
            if status == models.ItemStatus.ok:
                status = models.ItemStatus.pending
            # If we explicitly attempted a download for missing/forced media, drop the stale path.
            if force_download or not item.file_path or existing_extra.get("primary_image_is_avatar"):
                file_path = None
                thumbnail_path = None
        else:
            if downloaded_path:
                file_path = downloaded_path
                thumbnail_path = None

    final_title = item.title
    final_description = item.description
    final_text_content = item.text_content
    if update_text:
        final_title = metadata.title or item.title or normalized.url
        final_description = metadata.description if metadata.description is not None else item.description
        final_text_content = metadata.text_content if metadata.text_content is not None else item.text_content

    merged_extra = {**existing_extra, **(metadata.extra or {})}
    refresh_meta = dict(merged_extra.get("refresh") or {})
    refresh_meta["last_refreshed_at"] = datetime.now(timezone.utc).isoformat()
    if metadata.image_url:
        refresh_meta["last_image_url"] = metadata.image_url
    if metadata.error:
        refresh_meta["last_refresh_error"] = metadata.error
    if image_error:
        refresh_meta["last_image_error"] = image_error
    merged_extra["refresh"] = refresh_meta

    # Preserve existing non-URL derived fields unless explicitly updating text.
    item.title = final_title
    item.description = final_description
    item.text_content = final_text_content
    item.status = status
    item.source_url = normalized.url
    item.origin_domain = normalized.domain
    item.file_path = file_path
    item.thumbnail_path = thumbnail_path
    item.extra = merged_extra
    new_type = item.type
    if metadata.item_type and (item.type == models.ItemType.url or metadata.item_type != models.ItemType.url):
        new_type = metadata.item_type
    item.type = new_type

    db.add(item)
    if commit:
        db.commit()
        db.refresh(item)
    else:
        db.flush()
    return item


def _download_primary_image(
    image_url: str,
    *,
    image_get: metadata_service.HttpGetter | None = None,
) -> tuple[str | None, str | None]:
    getter = image_get or httpx.get
    try:
        response = getter(image_url, timeout=IMAGE_TIMEOUT)
    except httpx.HTTPError as exc:  # pragma: no cover
        return None, str(exc)

    status = getattr(response, "status_code", None)
    if status is not None and status >= 400:
        return None, f"HTTP {status}"

    content = getattr(response, "content", None)
    if not content:
        return None, "Empty image response"

    headers = getattr(response, "headers", {}) or {}
    content_type = headers.get("content-type") or headers.get("Content-Type") or ""
    if content_type and not content_type.lower().startswith("image/"):
        return None, f"Unsupported content-type {content_type}"

    ext = _pick_extension(image_url, getattr(response, "headers", {}))
    rel_path = storage.build_image_path(uuid.uuid4(), variant="url", ext=ext)
    with storage.FileWriteGuard() as guard:
        absolute = guard.track_relative(rel_path)
        absolute.write_bytes(content)
    return rel_path, None


def _pick_extension(image_url: str, headers: Mapping[str, str] | None) -> str:
    if headers:
        content_type = headers.get("content-type") or headers.get("Content-Type")
        if content_type:
            guess = mimetypes.guess_extension(content_type.split(";")[0].strip())
            if guess:
                return guess.lstrip(".")

    _, ext = os.path.splitext(image_url)
    if ext:
        return ext.lstrip(".")
    return "jpg"


def _maybe_apply_twitter_fallback(domain: str, url: str, metadata: metadata_service.MetadataResult) -> None:
    normalized = domain.lower()
    if not (normalized.endswith("twitter.com") or normalized.endswith("x.com")):
        return
    fallback_fn = getattr(url_extractors, "_twitter_oembed_fallback", None)
    if not fallback_fn:
        return
    try:
        fallback = fallback_fn(url)
    except Exception:  # pragma: no cover - defensive
        return
    if not fallback:
        return
    metadata.title = metadata.title or fallback.get("text")
    metadata.description = metadata.description or fallback.get("text")
    if not url_extractors._looks_like_image_url(metadata.image_url):
        metadata.image_url = fallback.get("image_url") or metadata.image_url
    extra = metadata.extra or {}
    if fallback.get("author") and not extra.get("author"):
        extra["author"] = fallback["author"]
    if fallback.get("timestamp") and not extra.get("timestamp"):
        extra["timestamp"] = fallback["timestamp"]
    if fallback.get("text") and not extra.get("tweet_text"):
        extra["tweet_text"] = fallback["text"]
    metadata.extra = extra
