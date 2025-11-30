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


def ensure_relative(path: Path) -> str:
    base = _storage_root()
    target = path.resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Path is outside of STORAGE_ROOT")
    return str(target.relative_to(base))

