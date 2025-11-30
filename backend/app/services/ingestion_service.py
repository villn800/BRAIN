from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from typing import Mapping

import httpx
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import storage, urls
from . import items_service, metadata_service, url_extractors

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
    if metadata.image_url:
        file_path, image_error = _download_primary_image(
            metadata.image_url,
            image_get=image_get,
        )
        if image_error:
            logger.warning("Failed to download image for %s: %s", normalized.url, image_error)
            if status == models.ItemStatus.ok:
                status = models.ItemStatus.pending

    item_payload = schemas.ItemCreate(
        title=final_title,
        description=metadata.description,
        type=metadata.item_type or models.ItemType.url,
        status=status,
        source_url=normalized.url,
        origin_domain=normalized.domain,
        file_path=file_path,
    )

    item = items_service.create_item(db, user, item_payload)

    if payload.tags:
        items_service.set_item_tags(db, user, item, payload.tags)

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