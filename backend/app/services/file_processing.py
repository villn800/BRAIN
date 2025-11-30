from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from PIL import Image
from PyPDF2 import PdfReader

from .. import models
from ..core import storage
from ..core.config import Settings, get_settings

logger = logging.getLogger(__name__)

IMAGE_TYPE_TO_EXTENSION: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}
IMAGE_EXTENSION_TO_TYPE: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}
PDF_CONTENT_TYPES = {"application/pdf"}

CHUNK_SIZE = 1024 * 1024


class UploadTooLargeError(Exception):
    """Raised when an uploaded file exceeds the configured limit."""


class UploadProcessingError(Exception):
    """Raised when an uploaded file cannot be processed."""


@dataclass(slots=True)
class FileProcessingResult:
    item_type: models.ItemType
    file_path: str
    thumbnail_path: str | None = None
    text_content: str | None = None
    status: models.ItemStatus = models.ItemStatus.ok
    content_type: str | None = None
    file_size_bytes: int = 0
    original_filename: str | None = None


def detect_image_media(upload: UploadFile) -> tuple[str, str] | None:
    """Return (content_type, extension) if the upload is a supported image."""
    content_type = (upload.content_type or "").lower()
    if content_type in IMAGE_TYPE_TO_EXTENSION:
        return content_type, IMAGE_TYPE_TO_EXTENSION[content_type]

    ext = _extension_from_filename(upload.filename)
    if ext and ext in IMAGE_EXTENSION_TO_TYPE:
        normalized_ext = "jpg" if ext == "jpeg" else ext
        return IMAGE_EXTENSION_TO_TYPE[ext], normalized_ext
    return None


def detect_pdf_media(upload: UploadFile) -> tuple[str, str] | None:
    """Return (content_type, extension) if the upload is a supported PDF."""
    content_type = (upload.content_type or "").lower()
    if content_type in PDF_CONTENT_TYPES:
        return content_type, "pdf"
    ext = _extension_from_filename(upload.filename)
    if ext == "pdf":
        return "application/pdf", "pdf"
    return None


def process_image_upload(
    upload: UploadFile,
    *,
    guard: storage.FileWriteGuard,
    settings: Settings | None = None,
    item_id: UUID | None = None,
) -> FileProcessingResult:
    media = detect_image_media(upload)
    if media is None:
        raise UploadProcessingError("Unsupported image format")

    content_type, ext = media
    cfg = settings or get_settings()
    file_uuid = item_id or uuid4()
    rel_original = storage.build_image_path(file_uuid, variant="original", ext=ext)
    original_path = guard.track_relative(rel_original)
    file_size = _save_upload_file(upload, original_path, max_bytes=cfg.MAX_UPLOAD_BYTES)

    rel_thumb = storage.build_thumbnail_path(file_uuid, ext="jpg")
    thumb_path = guard.track_relative(rel_thumb)
    _create_thumbnail(original_path, thumb_path, cfg.THUMBNAIL_SIZE, cfg.THUMBNAIL_QUALITY)

    return FileProcessingResult(
        item_type=models.ItemType.image,
        file_path=rel_original,
        thumbnail_path=rel_thumb,
        status=models.ItemStatus.ok,
        content_type=content_type,
        file_size_bytes=file_size,
        original_filename=upload.filename,
    )


def process_pdf_upload(
    upload: UploadFile,
    *,
    guard: storage.FileWriteGuard,
    settings: Settings | None = None,
    item_id: UUID | None = None,
) -> FileProcessingResult:
    media = detect_pdf_media(upload)
    if media is None:
        raise UploadProcessingError("Unsupported PDF upload")

    content_type, ext = media
    cfg = settings or get_settings()
    file_uuid = item_id or uuid4()
    rel_pdf = storage.build_pdf_path(file_uuid, ext=ext)
    pdf_path = guard.track_relative(rel_pdf)
    file_size = _save_upload_file(upload, pdf_path, max_bytes=cfg.MAX_UPLOAD_BYTES)
    text_content, had_error = extract_pdf_text(pdf_path, max_chars=cfg.PDF_TEXT_MAX_CHARS)
    status = models.ItemStatus.pending if had_error else models.ItemStatus.ok

    return FileProcessingResult(
        item_type=models.ItemType.pdf,
        file_path=rel_pdf,
        status=status,
        text_content=text_content,
        content_type=content_type,
        file_size_bytes=file_size,
        original_filename=upload.filename,
    )


def extract_pdf_text(path: Path, *, max_chars: int | None = None) -> tuple[str | None, bool]:
    """Extract textual content from a PDF, returning (text, had_error)."""
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:  # pragma: no cover - extremely unlikely
                logger.warning("PDF %s is encrypted and cannot be read", path)
                return None, True
        parts: list[str] = []
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # pragma: no cover - PyPDF2 edge cases
                logger.warning("Failed to extract text from page: %s", exc)
                return None, True
            if text:
                parts.append(text.strip())
        combined = "\n".join(part for part in parts if part).strip()
        if not combined:
            return None, False
        if max_chars and len(combined) > max_chars:
            combined = combined[:max_chars]
        return combined, False
    except Exception as exc:  # pragma: no cover
        logger.warning("PDF extraction failed for %s: %s", path, exc)
        return None, True


def _save_upload_file(upload: UploadFile, destination: Path, *, max_bytes: int) -> int:
    upload.file.seek(0)
    size = 0
    with destination.open("wb") as target:
        while True:
            chunk = upload.file.read(CHUNK_SIZE)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise UploadTooLargeError(
                    f"File exceeds maximum allowed size of {max_bytes} bytes"
                )
            target.write(chunk)
    upload.file.seek(0)
    return size


def _create_thumbnail(
    original_path: Path,
    thumbnail_path: Path,
    max_size: int,
    quality: int,
) -> None:
    try:
        with Image.open(original_path) as image:
            image.load()
            image = image.convert("RGB")
            image.thumbnail((max_size, max_size), resample=Image.LANCZOS)
            image.save(thumbnail_path, format="JPEG", quality=quality, optimize=True)
    except Exception as exc:  # pragma: no cover - Pillow edge cases
        raise UploadProcessingError(f"Unable to create thumbnail: {exc}") from exc


def _extension_from_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    name = filename.strip().lower()
    if not name or "." not in name:
        return None
    return name.rsplit(".", 1)[-1]