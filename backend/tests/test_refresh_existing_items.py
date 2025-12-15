from __future__ import annotations

from uuid import uuid4

from app import models, schemas
from app.database import SessionLocal
from app.services import ingestion_service, items_service, metadata_service


def _create_user(db) -> models.User:
    user = models.User(
        email=f"refresh-{uuid4().hex[:8]}@example.com",
        username=f"refresh_{uuid4().hex[:8]}",
        password_hash="hash",
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _basic_fetch(url: str, **_: object) -> metadata_service.HtmlFetchResult:
    return metadata_service.HtmlFetchResult(html="<html></html>", error=None)


def test_refresh_updates_avatar_flag(monkeypatch, app_client_factory):
    app_client_factory()
    db = SessionLocal()
    try:
        user = _create_user(db)
        item = items_service.create_item(
            db,
            user,
            schemas.ItemCreate(
                title="Original",
                type=models.ItemType.tweet,
                source_url="https://x.com/user/status/1",
                extra={"primary_image_is_avatar": True},
            ),
        )

        monkeypatch.setattr(ingestion_service.metadata_service, "fetch_html", _basic_fetch)

        def fake_extract(domain: str, url: str, html: str | None):
            return metadata_service.MetadataResult(
                url=url,
                title="New",
                description="New description",
                item_type=models.ItemType.tweet,
                extra={"primary_image_is_avatar": False},
            )

        monkeypatch.setattr(ingestion_service.url_extractors, "extract_for_domain", fake_extract)

        refreshed = ingestion_service.refresh_url_item(db, user, item)
        assert refreshed.extra["primary_image_is_avatar"] is False
        # update_text defaults to False, so title is preserved
        assert refreshed.title == "Original"
    finally:
        db.close()


def test_refresh_downloads_image_when_missing(monkeypatch, app_client_factory):
    app_client_factory()
    db = SessionLocal()
    try:
        user = _create_user(db)
        item = items_service.create_item(
            db,
            user,
            schemas.ItemCreate(
                title="Missing media",
                type=models.ItemType.tweet,
                source_url="https://twitter.com/user/status/2",
            ),
        )

        monkeypatch.setattr(ingestion_service.metadata_service, "fetch_html", _basic_fetch)

        def fake_extract(domain: str, url: str, html: str | None):
            return metadata_service.MetadataResult(
                url=url,
                title="Tweet title",
                description="Tweet body",
                image_url="https://pbs.twimg.com/media/example.jpg",
                item_type=models.ItemType.tweet,
                extra={"primary_image_is_avatar": False},
            )

        monkeypatch.setattr(ingestion_service.url_extractors, "extract_for_domain", fake_extract)
        monkeypatch.setattr(
            ingestion_service,
            "_download_primary_image",
            lambda image_url, **_: ("uploads/images/new.jpg", None),
        )

        refreshed = ingestion_service.refresh_url_item(db, user, item)
        assert refreshed.file_path == "uploads/images/new.jpg"
        assert refreshed.status == models.ItemStatus.ok
    finally:
        db.close()


def test_refresh_preserves_tags(monkeypatch, app_client_factory):
    app_client_factory()
    db = SessionLocal()
    try:
        user = _create_user(db)
        item = items_service.create_item(
            db,
            user,
            schemas.ItemCreate(
                title="Tagged",
                type=models.ItemType.tweet,
                source_url="https://x.com/user/status/3",
            ),
        )
        items_service.set_item_tags(db, user, item, ["Design", "UX"])

        monkeypatch.setattr(ingestion_service.metadata_service, "fetch_html", _basic_fetch)
        monkeypatch.setattr(
            ingestion_service.url_extractors,
            "extract_for_domain",
            lambda domain, url, html: metadata_service.MetadataResult(
                url=url,
                title="New title",
                description="New description",
                image_url=None,
                item_type=models.ItemType.tweet,
                extra={"primary_image_is_avatar": False},
            ),
        )

        refreshed = ingestion_service.refresh_url_item(db, user, item)
        assert {tag.name for tag in refreshed.tags} == {"Design", "UX"}
    finally:
        db.close()


def test_refresh_respects_update_text_flag(monkeypatch, app_client_factory):
    app_client_factory()
    db = SessionLocal()
    try:
        user = _create_user(db)
        item = items_service.create_item(
            db,
            user,
            schemas.ItemCreate(
                title="User title",
                description="User description",
                type=models.ItemType.tweet,
                source_url="https://twitter.com/user/status/4",
            ),
        )

        monkeypatch.setattr(ingestion_service.metadata_service, "fetch_html", _basic_fetch)
        metadata = metadata_service.MetadataResult(
            url=str(item.source_url),
            title="Fetched title",
            description="Fetched description",
            item_type=models.ItemType.tweet,
            extra={"primary_image_is_avatar": False},
        )
        monkeypatch.setattr(
            ingestion_service.url_extractors,
            "extract_for_domain",
            lambda domain, url, html: metadata,
        )

        untouched = ingestion_service.refresh_url_item(db, user, item, update_text=False)
        assert untouched.title == "User title"
        assert untouched.description == "User description"

        updated = ingestion_service.refresh_url_item(db, user, untouched, update_text=True)
        assert updated.title == "Fetched title"
        assert updated.description == "Fetched description"
    finally:
        db.close()
