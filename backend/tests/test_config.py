from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings, reset_settings


def test_settings_respect_env_overrides(monkeypatch, tmp_path):
    storage_dir = tmp_path / "custom_storage"
    storage_dir.mkdir()

    monkeypatch.setenv("PROJECT_NAME", "Custom Project")
    monkeypatch.setenv("API_V1_PREFIX", "v2")
    monkeypatch.setenv("STORAGE_ROOT", str(storage_dir))
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "42")

    reset_settings()

    settings = get_settings()

    assert settings.PROJECT_NAME == "Custom Project"
    assert settings.API_V1_PREFIX == "/v2"
    assert settings.STORAGE_ROOT == Path(storage_dir)
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 42

    reset_settings()


def test_cors_origins_support_comma_separated_strings(monkeypatch):
    monkeypatch.setenv(
        "CORS_ALLOW_ORIGINS",
        "[\"http://localhost:5173\", \"https://vault.example.com\"]",
    )

    reset_settings()

    settings = get_settings()

    assert settings.CORS_ALLOW_ORIGINS == [
        "http://localhost:5173",
        "https://vault.example.com",
    ]

    reset_settings()