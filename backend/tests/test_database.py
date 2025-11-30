from __future__ import annotations

from unittest.mock import MagicMock

from sqlalchemy import text

from app import database
from app.core.config import reset_settings


def test_get_db_yields_session_and_closes(monkeypatch, tmp_path):
    db_path = tmp_path / "db.sqlite3"
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_ROOT", str(storage_dir))

    reset_settings()
    database.configure_engine()
    database.Base.metadata.create_all(bind=database.get_engine())

    real_session = database.SessionLocal()
    close_spy = MagicMock()
    real_session.close = close_spy

    monkeypatch.setattr(database, "SessionLocal", lambda: real_session)

    gen = database.get_db()
    session = next(gen)

    assert session.execute(text("SELECT 1")).scalar_one() == 1

    gen.close()

    close_spy.assert_called_once_with()