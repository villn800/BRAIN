from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PIL import Image

from app import models
from app.core import storage
from app.core.config import get_settings
from app.services import file_processing
from tests import utils


def test_process_image_upload_generates_thumbnail(app_client_factory) -> None:
    app_client_factory()
    upload = utils.make_upload_file("square.png", "image/png", utils.make_png_bytes((96, 64)))

    with storage.FileWriteGuard() as guard:
        result = file_processing.process_image_upload(upload, guard=guard, item_id=uuid4())

    assert result.item_type == models.ItemType.image
    assert result.thumbnail_path is not None
    assert result.content_type == "image/png"
    settings = get_settings()
    original_path = storage.resolve_storage_path(result.file_path, create_parents=False)
    thumb_path = storage.resolve_storage_path(result.thumbnail_path, create_parents=False)
    assert original_path.exists()
    assert thumb_path.exists()
    assert result.file_size_bytes > 0
    with Image.open(thumb_path) as thumbnail:
        assert thumbnail.width <= settings.THUMBNAIL_SIZE
        assert thumbnail.height <= settings.THUMBNAIL_SIZE


def test_process_pdf_upload_extracts_text(app_client_factory) -> None:
    app_client_factory()
    pdf_bytes = utils.make_pdf_bytes("Hello PDF World")
    upload = utils.make_upload_file("doc.pdf", "application/pdf", pdf_bytes)

    with storage.FileWriteGuard() as guard:
        result = file_processing.process_pdf_upload(upload, guard=guard, item_id=uuid4())

    assert result.item_type == models.ItemType.pdf
    assert result.text_content is not None
    assert "Hello PDF World" in result.text_content
    assert result.status == models.ItemStatus.ok
    pdf_path = storage.resolve_storage_path(result.file_path, create_parents=False)
    assert pdf_path.exists()


def test_file_write_guard_cleans_partial_files_on_error(app_client_factory) -> None:
    _, storage_root = app_client_factory()
    rel_path = "uploads/images/cleanup_test.txt"
    try:
        with storage.FileWriteGuard() as guard:
            path = guard.track_relative(rel_path)
            path.write_text("temp")
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    assert not (storage_root / Path(rel_path)).exists()