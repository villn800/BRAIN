from __future__ import annotations

import io

import pytest
from PIL import Image

from app import models
from app.core.config import get_settings
from app.services import items_service
from tests import utils


def test_upload_image_creates_item_with_thumbnail(app_client_factory) -> None:
    client, storage_root = app_client_factory()
    headers = utils.auth_headers(client)
    image_bytes = utils.make_png_bytes()

    response = client.post(
        "/api/items/upload",
        headers=headers,
        data={"title": "Mood Board", "tags_csv": "Design,Reference"},
        files=[("file", ("sample.png", io.BytesIO(image_bytes), "image/png"))],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["type"] == models.ItemType.image.value
    assert body["thumbnail_path"] is not None
    assert body["file_path"].startswith("uploads/")
    assert {tag["name"] for tag in body["tags"]} == {"Design", "Reference"}

    original = storage_root / body["file_path"]
    thumbnail = storage_root / body["thumbnail_path"]
    assert original.exists()
    assert thumbnail.exists()
    settings = get_settings()
    with Image.open(thumbnail) as thumb:
        assert thumb.width <= settings.THUMBNAIL_SIZE
        assert thumb.height <= settings.THUMBNAIL_SIZE


def test_upload_pdf_extracts_text_content(app_client_factory) -> None:
    client, storage_root = app_client_factory()
    headers = utils.auth_headers(client)
    pdf_bytes = utils.make_pdf_bytes("Upload Pipeline")

    response = client.post(
        "/api/items/upload",
        headers=headers,
        data={"description": "Spec doc"},
        files=[("file", ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf"))],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["type"] == models.ItemType.pdf.value
    assert body["thumbnail_path"] is None
    assert body["text_content"] and "Upload Pipeline" in body["text_content"]
    assert body["status"] == models.ItemStatus.ok.value
    pdf_path = storage_root / body["file_path"]
    assert pdf_path.exists()


def test_upload_rejects_invalid_type(app_client_factory) -> None:
    client, _ = app_client_factory()
    headers = utils.auth_headers(client)

    response = client.post(
        "/api/items/upload",
        headers=headers,
        files=[("file", ("notes.txt", io.BytesIO(b"plain"), "text/plain"))],
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.text


def test_upload_rejects_oversized_file(app_client_factory) -> None:
    client, _ = app_client_factory(extra_env={"MAX_UPLOAD_BYTES": "1024"})
    headers = utils.auth_headers(client)

    response = client.post(
        "/api/items/upload",
        headers=headers,
        files=[("file", ("big.png", io.BytesIO(b"a" * 2048), "image/png"))],
    )
    assert response.status_code == 400


def test_upload_cleans_files_when_db_fails(app_client_factory, monkeypatch) -> None:
    client, storage_root = app_client_factory()
    headers = utils.auth_headers(client)
    image_bytes = utils.make_png_bytes()

    def _boom(*args, **kwargs):
        raise RuntimeError("db failure")

    monkeypatch.setattr(items_service, "create_item", _boom)

    with pytest.raises(RuntimeError):
        client.post(
            "/api/items/upload",
            headers=headers,
            files=[("file", ("failure.png", io.BytesIO(image_bytes), "image/png"))],
        )
    assert not any(path.is_file() for path in storage_root.rglob("*"))