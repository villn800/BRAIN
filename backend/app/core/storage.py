from __future__ import annotations

from pathlib import Path
from uuid import UUID

from .config import get_settings


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

