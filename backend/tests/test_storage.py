from __future__ import annotations

from uuid import uuid4

import pytest

from app.core import storage


def test_storage_path_builders_are_relative() -> None:
    item_id = uuid4()
    image_path = storage.build_image_path(item_id)
    thumb_path = storage.build_thumbnail_path(item_id)
    pdf_path = storage.build_pdf_path(item_id)
    raw_path = storage.build_raw_asset_path(item_id, "example.bin")

    for path in (image_path, thumb_path, pdf_path, raw_path):
        assert not path.startswith("/"), "paths must be relative to STORAGE_ROOT"
        assert ".." not in path


def test_resolve_storage_path_and_normalize(app_client_factory) -> None:
    _, storage_root = app_client_factory()
    rel_path = f"uploads/test/{uuid4().hex}.txt"
    resolved = storage.resolve_storage_path(rel_path)
    assert str(resolved).startswith(str(storage_root))
    assert resolved.parent.exists()

    absolute = resolved
    normalized = storage.normalize_relative_path(str(absolute))
    assert normalized == rel_path


def test_resolve_storage_path_blocks_traversal(app_client_factory) -> None:
    app_client_factory()
    with pytest.raises(ValueError):
        storage.resolve_storage_path("../../etc/passwd")

    with pytest.raises(ValueError):
        storage.normalize_relative_path("../../etc/passwd")