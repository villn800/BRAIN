from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.services import ingestion_service, metadata_service
from app import models

BOOTSTRAP = {
    "email": "ingest@example.com",
    "username": "ingester",
    "password": "SecurePass123!",
}
FIXTURES = Path(__file__).parent / "fixtures" / "twitter"


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


def test_twitter_video_ingestion_persists_extra(monkeypatch, app_client_factory):
    client, _ = app_client_factory()
    headers = _auth_headers(client)
    html = (FIXTURES / "video_simple.html").read_text()

    monkeypatch.setattr(
        ingestion_service.metadata_service,
        "fetch_html",
        lambda url, **_: metadata_service.HtmlFetchResult(html=html),
    )
    monkeypatch.setattr(
        ingestion_service,
        "_download_primary_image",
        lambda image_url, **_: ("uploads/images/video_poster.jpg", None),
    )

    response = client.post(
        "/api/items/url",
        json={"url": "https://twitter.com/user/status/555"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["extra"]["media_kind"] == "video"
    assert body["extra"]["video_url"].endswith(".mp4")
    assert body["extra"]["video_type"] == "mp4"
    assert body["file_path"] == "uploads/images/video_poster.jpg"
    assert body["type"] == models.ItemType.tweet.value


def test_twitter_headless_ingestion_persists_video_extra(monkeypatch, app_client_factory):
    client, _ = app_client_factory()
    headers = _auth_headers(client)
    html = "<html><head><meta property='og:title' content='Author (@handle)'></head></html>"

    class FakeSettings:
        TWITTER_HEADLESS_ENABLED = True
        TWITTER_HEADLESS_TIMEOUT_SECS = 1.0

    monkeypatch.setattr(
        ingestion_service.metadata_service,
        "fetch_html",
        lambda url, **_: metadata_service.HtmlFetchResult(html=html),
    )
    monkeypatch.setattr(
        ingestion_service.url_extractors,
        "get_settings",
        lambda: FakeSettings(),
    )
    monkeypatch.setattr(
        ingestion_service.url_extractors,
        "resolve_twitter_video_headless",
        lambda url, timeout=0.0: {
            "video_url": "https://video.twimg.com/ext_tw_video/1842312345678901234/pu/vid/720x720/abcdEFGH.mp4?tag=21",
            "video_type": "mp4",
            "poster_url": "https://pbs.twimg.com/media/poster.jpg",
        },
    )
    monkeypatch.setattr(
        ingestion_service,
        "_download_primary_image",
        lambda image_url, **_: ("uploads/images/twitter_poster.jpg", None),
    )

    response = client.post(
        "/api/items/url",
        json={"url": "https://x.com/user/status/999"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["extra"]["media_kind"] == "video"
    assert body["extra"]["video_url"].startswith("https://video.twimg.com/")
    assert ".mp4" in body["extra"]["video_url"]
    assert body["file_path"] == "uploads/images/twitter_poster.jpg"


def test_twitter_hls_ingestion_falls_back_to_image(monkeypatch, app_client_factory):
    client, _ = app_client_factory()
    headers = _auth_headers(client)
    html = (FIXTURES / "video_hls.html").read_text()

    monkeypatch.setattr(
        ingestion_service.metadata_service,
        "fetch_html",
        lambda url, **_: metadata_service.HtmlFetchResult(html=html),
    )
    monkeypatch.setattr(
        ingestion_service,
        "_download_primary_image",
        lambda image_url, **_: ("uploads/images/hls_poster.jpg", None),
    )

    response = client.post(
        "/api/items/url",
        json={"url": "https://x.com/user/status/777"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["extra"]["media_kind"] == "image"
    assert body["extra"].get("video_url") is None
    assert body["file_path"] == "uploads/images/hls_poster.jpg"


def test_twitter_ingestion_prefers_media_over_avatar(monkeypatch, app_client_factory):
    client, _ = app_client_factory()
    headers = _auth_headers(client)
    html = (FIXTURES / "quote_tweet_with_media_juniorkingpp.html").read_text()

    monkeypatch.setattr(
        ingestion_service.metadata_service,
        "fetch_html",
        lambda url, **_: metadata_service.HtmlFetchResult(html=html),
    )
    captured: dict[str, str] = {}

    def _fake_download(image_url: str, **kwargs):
        captured["url"] = image_url
        return ("uploads/images/media.jpg", None)

    monkeypatch.setattr(
        ingestion_service,
        "_download_primary_image",
        _fake_download,
    )

    response = client.post(
        "/api/items/url",
        json={"url": "https://x.com/juniorkingpp/status/1996087779269464125"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert captured["url"].startswith("https://pbs.twimg.com/media/")
    body = response.json()
    assert body["file_path"] == "uploads/images/media.jpg"


def test_twitter_ingestion_uses_card_image(monkeypatch, app_client_factory):
    client, _ = app_client_factory()
    headers = _auth_headers(client)
    html = (FIXTURES / "quote_tweet_or_card_girlflours.html").read_text()

    monkeypatch.setattr(
        ingestion_service.metadata_service,
        "fetch_html",
        lambda url, **_: metadata_service.HtmlFetchResult(html=html),
    )
    captured: dict[str, str] = {}

    def _fake_download(image_url: str, **kwargs):
        captured["url"] = image_url
        return ("uploads/images/card.jpg", None)

    monkeypatch.setattr(
        ingestion_service,
        "_download_primary_image",
        _fake_download,
    )

    response = client.post(
        "/api/items/url",
        json={"url": "https://x.com/girlflours/status/1996331045344735356"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert captured["url"].startswith("https://pbs.twimg.com/media/")
    body = response.json()
    assert body["file_path"] == "uploads/images/card.jpg"


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
