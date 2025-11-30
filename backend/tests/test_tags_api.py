from __future__ import annotations

from tests import utils


def _create_item(client, headers, title: str) -> str:
    response = client.post(
        "/api/items",
        json={"title": title, "type": "url"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_create_and_list_tags_with_counts(app_client_factory) -> None:
    client, _ = app_client_factory()
    headers = utils.auth_headers(client)
    first = _create_item(client, headers, "Mood")
    second = _create_item(client, headers, "Poster")

    design = client.post("/api/tags", json={"name": "Design"}, headers=headers)
    assert design.status_code == 201
    poster = client.post("/api/tags", json={"name": "Poster"}, headers=headers)
    assert poster.status_code == 201

    client.put(f"/api/items/{first}/tags", json={"tags": ["Design"]}, headers=headers)
    client.put(f"/api/items/{second}/tags", json={"tags": ["Design", "Poster"]}, headers=headers)

    response = client.get("/api/tags", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body[0]["name"] == "Design"
    assert body[0]["item_count"] == 2
    assert body[1]["name"] == "Poster"
    assert body[1]["item_count"] == 1


def test_duplicate_tag_creation_rejected(app_client_factory) -> None:
    client, _ = app_client_factory()
    headers = utils.auth_headers(client)

    first = client.post("/api/tags", json={"name": "Mood"}, headers=headers)
    assert first.status_code == 201
    dup = client.post("/api/tags", json={"name": "Mood"}, headers=headers)
    assert dup.status_code == 400


def test_delete_tag_and_get_item_tags_endpoint(app_client_factory) -> None:
    client, _ = app_client_factory()
    headers = utils.auth_headers(client)

    item_id = _create_item(client, headers, "Reference")
    created = client.post("/api/tags", json={"name": "Archive"}, headers=headers)
    tag_id = created.json()["id"]

    client.put(f"/api/items/{item_id}/tags", json={"tags": ["Archive"]}, headers=headers)
    tag_list = client.get(f"/api/items/{item_id}/tags", headers=headers)
    assert [tag["name"] for tag in tag_list.json()] == ["Archive"]

    delete_resp = client.delete(f"/api/tags/{tag_id}", headers=headers)
    assert delete_resp.status_code == 204

    tag_list = client.get(f"/api/items/{item_id}/tags", headers=headers)
    assert tag_list.status_code == 200
    assert tag_list.json() == []