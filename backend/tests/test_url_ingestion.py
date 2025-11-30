from __future__ import annotations

from uuid import uuid4

import pytest

from app.services import ingestion_service, metadata_service
from app import models

BOOTSTRAP = {
    "email": "ingest@example.com",
    "username": "ingester",
    "password": "SecurePass123!",
}


def _auth_headers(client):
    client.post("/api/auth/bootstrap", json=BOOTSTRAP)
    token = client.post(
        "/api/auth/login",
        json={"identifier": BOOTSTRAP["email"], "password": BOOTSTRAP["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_generic_url_ingestion_creates_item(app_client_factory, monkeypatch):
    client, _ = app_client_factory()
    headers = _auth_headers(client)

    html = """
    <html>
      <head>
        <title>Example Page</title>
        <meta name='description' content='Sample description'>
        <meta property='og:image' content='https://cdn.example.com/img.jpg'>
      </head>
    </html>
    """

    monkeypatch.setattr(
        ingestion_service.metadata_service,
        "fetch_html",
        lambda url, **_: metadata_service.HtmlFetchResult(html=html),
    )
    monkeypatch.setattr(
        ingestion_service,
        "_download_primary_image",
        lambda image_url, **_: ("uploads/images/mock.jpg", None),
    )

    response = client.post(
        "/api/items/url",
        json={"url": "example.com/test", "tags": ["Design"]},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["origin_domain"] == "example.com"
    assert body["title"] == "Example Page"
    assert body["file_path"] == "uploads/images/mock.jpg"
    assert [tag["name"] for tag in body["tags"]] == ["Design"]


def test_twitter_ingestion_sets_item_type(monkeypatch, app_client_factory):
    client, _ = app_client_factory()
    headers = _auth_headers(client)

    html = """
    <meta property='og:description' content='Tweet body'>
    <meta property='og:title' content='Author (@handle)'>
    <meta property='og:image' content='https://cdn.twitter.com/img.jpg'>
    """

    monkeypatch.setattr(
        ingestion_service.metadata_service,
        "fetch_html",
        lambda url, **_: metadata_service.HtmlFetchResult(html=html),
    )
    monkeypatch.setattr(
        ingestion_service,
        "_download_primary_image",
        lambda *args, **kwargs: (None, "no image"),
    )

    response = client.post(
        "/api/items/url",
        json={"url": "https://twitter.com/user/status/42"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == models.ItemType.tweet.value
    assert body["status"] == models.ItemStatus.pending.value


def test_ingestion_handles_fetch_failure(monkeypatch, app_client_factory):
    client, _ = app_client_factory()
    headers = _auth_headers(client)

    monkeypatch.setattr(
        ingestion_service.metadata_service,
        "fetch_html",
        lambda url, **_: metadata_service.HtmlFetchResult(html=None, error="timeout"),
    )

    response = client.post(
        "/api/items/url",
        json={"url": "https://example.com/fail"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == models.ItemStatus.failed.value