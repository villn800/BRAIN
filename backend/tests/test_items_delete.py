from __future__ import annotations

from uuid import uuid4

from app import models
from app.database import SessionLocal
from tests import utils


def test_delete_item_requires_auth(app_client_factory):
    client, _ = app_client_factory()
    response = client.delete(f"/api/items/{uuid4()}")
    assert response.status_code == 401


def test_delete_item_removes_db_row_and_files(app_client_factory):
    client, storage_root = app_client_factory()
    headers = utils.auth_headers(client)

    rel_path = "uploads/images/delete_me.jpg"
    thumb_path = "uploads/images/delete_me_thumb.jpg"
    (storage_root / rel_path).parent.mkdir(parents=True, exist_ok=True)
    (storage_root / rel_path).write_text("primary")
    (storage_root / thumb_path).parent.mkdir(parents=True, exist_ok=True)
    (storage_root / thumb_path).write_text("thumb")

    create_response = client.post(
        "/api/items",
        json={
            "title": "Delete target",
            "type": "image",
            "file_path": rel_path,
            "thumbnail_path": thumb_path,
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    item_id = create_response.json()["id"]

    tag_response = client.put(
        f"/api/items/{item_id}/tags",
        json={"tags": ["Temp", "Ref"]},
        headers=headers,
    )
    assert tag_response.status_code == 200

    delete_response = client.delete(f"/api/items/{item_id}", headers=headers)
    assert delete_response.status_code == 204

    assert not (storage_root / rel_path).exists()
    assert not (storage_root / thumb_path).exists()

    follow_up = client.get(f"/api/items/{item_id}", headers=headers)
    assert follow_up.status_code == 404

    db = SessionLocal()
    try:
        assert db.query(models.Item).count() == 0
        assert db.query(models.ItemTag).count() == 0
    finally:
        db.close()
