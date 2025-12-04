from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from .config import get_settings

logger = logging.getLogger(__name__)


def _storage_root() -> Path:
    root = Path(get_settings().STORAGE_ROOT).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_storage_path(relative_path: str, *, create_parents: bool = True) -> Path:
    """Resolve a relative storage path under STORAGE_ROOT, preventing traversal."""
    normalized = relative_path.lstrip("/").strip()
    base = _storage_root()
    target = (base / normalized).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Attempted path traversal outside STORAGE_ROOT")
    if create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    return target


def build_image_path(item_id: UUID, variant: str = "original", ext: str = "jpg") -> str:
    """Return a relative path for storing item images."""
    return f"uploads/images/{item_id}_{variant}.{ext}"


def build_thumbnail_path(item_id: UUID, ext: str = "jpg") -> str:
    return build_image_path(item_id, variant="thumb", ext=ext)


def build_pdf_path(item_id: UUID, ext: str = "pdf") -> str:
    return f"uploads/pdfs/{item_id}.{ext}"


def build_raw_asset_path(item_id: UUID, filename: str) -> str:
    """Return a relative path for arbitrary/raw assets tied to an item."""
    sanitized_name = Path(filename).name
    if not sanitized_name:
        sanitized_name = "asset"
    return f"uploads/raw/{item_id}_{sanitized_name}"


def ensure_relative(path: Path) -> str:
    base = _storage_root()
    target = path.resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Path is outside of STORAGE_ROOT")
    return str(target.relative_to(base))


def normalize_relative_path(path: str | Path | None) -> str | None:
    """Normalize a provided path so only STORAGE_ROOT-relative strings are persisted."""
    if path is None:
        return None
    raw = str(path).strip()
    if not raw:
        return None

    base = _storage_root()
    candidate = Path(raw)
    if candidate.is_absolute():
        return ensure_relative(candidate)

    relative = raw.lstrip("/")
    resolved = (base / relative).resolve()
    if not str(resolved).startswith(str(base)):
        raise ValueError("Attempted path traversal outside STORAGE_ROOT")
    return str(resolved.relative_to(base))


def safe_remove_path(relative_path: str | None) -> None:
    """Best-effort removal of a STORAGE_ROOT-relative file."""
    if not relative_path:
        return
    try:
        target = resolve_storage_path(relative_path, create_parents=False)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.debug("Skipping delete for %s: %s", relative_path, exc)
        return
    try:
        target.unlink(missing_ok=True)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.debug("Failed to delete %s: %s", target, exc)


class FileWriteGuard:
    """Track files created during an operation and delete them if it fails."""

    def __init__(self) -> None:
        self._paths: list[Path] = []

    def track_relative(self, relative_path: str, *, create_parents: bool = True) -> Path:
        path = resolve_storage_path(relative_path, create_parents=create_parents)
        self._paths.append(path)
        return path

    def track(self, path: Path) -> Path:
        base = _storage_root()
        resolved = path.resolve()
        if not str(resolved).startswith(str(base)):
            raise ValueError("Path is outside of STORAGE_ROOT")
        self._paths.append(resolved)
        return resolved

    def cleanup(self) -> None:
        for path in reversed(self._paths):
            path.unlink(missing_ok=True)
        self._paths.clear()

    def __enter__(self) -> "FileWriteGuard":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.cleanup()
        else:
            self._paths.clear()
        return False
