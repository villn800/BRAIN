from __future__ import annotations

from pathlib import Path

import pytest

from app import models, schemas
from app.core.config import reset_settings
from app.core import urls
from app.database import Base, SessionLocal, configure_engine
from app.services import ingestion_service, items_service
from app.services.deepseek_client import DeepSeekTagResult
from scripts import import_liked_tweets_deepseek as importer

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "twitter" / "liked_tweets_sample.json"


def _bootstrap_db(monkeypatch, tmp_path):
    db_path = tmp_path / "tweets.db"
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    env = {
        "DATABASE_URL": f"sqlite:///{db_path}",
        "STORAGE_ROOT": str(storage_dir),
        "SECRET_KEY": "test-secret",
        "PROJECT_NAME": "Test",
        "API_V1_PREFIX": "/api",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    reset_settings()
    engine = configure_engine(env["DATABASE_URL"])
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = models.User(email="importer@example.com", username="importer", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)
    return engine


def _stub_ingest_url():
    def _fake_ingest(db, user, payload, **kwargs):
        normalized = urls.normalize_url(payload.url)
        item_payload = schemas.ItemCreate(
            title=payload.title or normalized.url,
            description=None,
            type=models.ItemType.url,
            status=models.ItemStatus.ok,
            source_url=normalized.url,
            origin_domain=normalized.domain,
        )
        item = items_service.create_item(db, user, item_payload)
        if payload.tags:
            items_service.set_item_tags(db, user, item, payload.tags)
        return item

    return _fake_ingest


def _stub_tag_result():
    return DeepSeekTagResult(tags=["design", "inspiration"], summary="Mock summary", category="creative")


def test_dry_run_prints_output(monkeypatch, capsys, tmp_path):
    _bootstrap_db(monkeypatch, tmp_path)
    tweets = importer._load_tweets(FIXTURE_PATH)  # noqa: SLF001

    monkeypatch.setattr(importer, "generate_tags_for_text", lambda *args, **kwargs: _stub_tag_result())

    exit_code = importer.process_tweets(
        tweets,
        user_email="importer@example.com",
        limit=1,
        dry_run=True,
    )

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "https://x.com" in captured
    assert "design" in captured
    with SessionLocal() as db:
        assert db.query(models.Item).count() == 0


def test_import_creates_items_and_tags(monkeypatch, tmp_path):
    _bootstrap_db(monkeypatch, tmp_path)
    tweets = importer._load_tweets(FIXTURE_PATH)  # noqa: SLF001

    monkeypatch.setattr(importer, "generate_tags_for_text", lambda *args, **kwargs: _stub_tag_result())
    monkeypatch.setattr(ingestion_service, "ingest_url", _stub_ingest_url())

    exit_code = importer.process_tweets(
        tweets,
        user_email="importer@example.com",
        limit=2,
        dry_run=False,
    )

    assert exit_code == 0
    with SessionLocal() as db:
        items = db.query(models.Item).all()
        assert len(items) == 2
        for item in items:
            assert item.origin_domain == "x.com"
            assert {t.name for t in item.tags} == {"design", "inspiration", "creative"}
