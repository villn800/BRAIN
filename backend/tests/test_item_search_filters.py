from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from app import models
from app.database import SessionLocal
from tests import utils


def _create_item(client, headers, **payload):
    base = {
        "title": payload.get("title", "Sample"),
        "type": payload.get("type", models.ItemType.url.value),
        "description": payload.get("description"),
        "text_content": payload.get("text_content"),
        "status": payload.get("status", models.ItemStatus.ok.value),
    }
    response = client.post("/api/items", json=base, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _set_created_at(item_id: str, value: datetime) -> None:
    db = SessionLocal()
    try:
        record = db.get(models.Item, UUID(item_id))
        assert record is not None
        record.created_at = value
        db.add(record)
        db.commit()
    finally:
        db.close()


def test_keyword_search_matches_all_text_fields(app_client_factory) -> None:
    client, _ = app_client_factory()
    headers = utils.auth_headers(client)

    first = _create_item(client, headers, title="Mood Board", description="Palette ideas")
    second = _create_item(client, headers, title="Poster", description="Retro vibes")
    third = _create_item(
        client,
        headers,
        title="Archive",
        type=models.ItemType.pdf.value,
        text_content="Deep dive into nostalgia",
    )

    resp = client.get("/api/items", headers=headers, params={"q": "mood"})
    assert [item["id"] for item in resp.json()] == [first["id"]]

    resp = client.get("/api/items", headers=headers, params={"q": "retro"})
    assert [item["id"] for item in resp.json()] == [second["id"]]

    resp = client.get("/api/items", headers=headers, params={"q": "nostalgia"})
    assert [item["id"] for item in resp.json()] == [third["id"]]


def test_type_and_date_filters_work_together(app_client_factory) -> None:
    client, _ = app_client_factory()
    headers = utils.auth_headers(client)

    image = _create_item(client, headers, title="Image", type=models.ItemType.image.value)
    pdf = _create_item(client, headers, title="Document", type=models.ItemType.pdf.value)
    url = _create_item(client, headers, title="Article", type=models.ItemType.url.value)

    now = datetime.now(timezone.utc)
    _set_created_at(image["id"], now - timedelta(days=3))
    _set_created_at(pdf["id"], now - timedelta(days=1))
    _set_created_at(url["id"], now)

    resp = client.get("/api/items", headers=headers, params={"type": models.ItemType.image.value})
    body = resp.json()
    assert [item["id"] for item in body] == [image["id"]]

    params = {
        "created_from": (now - timedelta(days=2)).isoformat(),
        "created_to": (now + timedelta(seconds=1)).isoformat(),
    }
    resp = client.get("/api/items", headers=headers, params=params)
    ids = [item["id"] for item in resp.json()]
    assert ids == [url["id"], pdf["id"]]

    params["type"] = models.ItemType.pdf.value
    resp = client.get("/api/items", headers=headers, params=params)
    ids = [item["id"] for item in resp.json()]
    assert ids == [pdf["id"]]


def test_tag_filter_accepts_single_and_multiple_tags(app_client_factory) -> None:
    client, _ = app_client_factory()
    headers = utils.auth_headers(client)

    mood = _create_item(client, headers, title="Mood Reference")
    poster = _create_item(client, headers, title="Poster Inspiration")

    resp = client.put(
        f"/api/items/{mood['id']}/tags",
        json={"tags": ["Design", "Color"]},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = client.put(
        f"/api/items/{poster['id']}/tags",
        json={"tags": ["Design", "Poster"]},
        headers=headers,
    )
    assert resp.status_code == 200

    resp = client.get("/api/items", headers=headers, params={"tag": "color"})
    ids = [item["id"] for item in resp.json()]
    assert ids == [mood["id"]]

    resp = client.get(
        "/api/items",
        headers=headers,
        params=[("tags", "design"), ("tags", "poster")],
    )
    ids = [item["id"] for item in resp.json()]
    assert ids == [poster["id"]]


def test_pagination_uses_limit_and_offset(app_client_factory) -> None:
    client, _ = app_client_factory()
    headers = utils.auth_headers(client)

    first = _create_item(client, headers, title="Alpha")
    second = _create_item(client, headers, title="Beta")
    third = _create_item(client, headers, title="Gamma")

    resp = client.get("/api/items", headers=headers, params={"limit": 1})
    assert [item["id"] for item in resp.json()] == [third["id"]]

    resp = client.get("/api/items", headers=headers, params={"limit": 1, "offset": 1})
    assert [item["id"] for item in resp.json()] == [second["id"]]

    resp = client.get("/api/items", headers=headers, params={"limit": 2, "offset": 1})
    assert [item["id"] for item in resp.json()] == [second["id"], first["id"]]