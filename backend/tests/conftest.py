from __future__ import annotations

from pathlib import Path
from typing import Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import reset_settings
from app.database import Base, configure_engine, get_engine
from app.main import create_app


@pytest.fixture
def app_client_factory(monkeypatch, tmp_path) -> Callable[..., tuple[TestClient, Path]]:
    """Create fully configured FastAPI TestClients backed by sqlite + temp storage."""

    clients: list[TestClient] = []

    def _factory(*, storage_exists: bool = True, extra_env: dict[str, str] | None = None) -> tuple[TestClient, Path]:
        env_dir = tmp_path / f"env_{uuid4().hex}"
        env_dir.mkdir()
        db_path = env_dir / "test.db"
        storage_dir = env_dir / "storage"
        if storage_exists:
            storage_dir.mkdir(parents=True)
        env_vars = {
            "DATABASE_URL": f"sqlite:///{db_path}",
            "STORAGE_ROOT": str(storage_dir),
            "SECRET_KEY": "test-secret-key",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "PROJECT_NAME": "Test BRAIN",
            "API_V1_PREFIX": "/api",
        }
        if extra_env:
            env_vars.update(extra_env)
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        reset_settings()
        configure_engine(env_vars["DATABASE_URL"])
        engine = get_engine()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        app = create_app()
        client = TestClient(app)
        clients.append(client)
        return client, storage_dir

    yield _factory

    for client in clients:
        client.close()