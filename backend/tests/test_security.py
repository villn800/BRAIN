from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.core import security
from app.core.config import reset_settings


def test_hash_and_verify_password_round_trip() -> None:
    password = "supersafe-pass123"
    hashed = security.hash_password(password)

    assert hashed != password
    assert security.verify_password(password, hashed)
    assert security.verify_password(password, hashed)  # re-verify uses cached salt
    assert not security.verify_password("bad-password", hashed)


def test_create_and_decode_access_token(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret-key")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5")
    reset_settings()

    token = security.create_access_token({"sub": "user-123", "scope": "test"})
    decoded = security.decode_access_token(token)

    assert decoded["sub"] == "user-123"
    assert decoded["scope"] == "test"


def test_decode_access_token_rejects_invalid(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret-key")
    reset_settings()

    with pytest.raises(HTTPException):
        security.decode_access_token("invalid-token")


def test_decode_access_token_rejects_expired(monkeypatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret-key")
    reset_settings()

    expired_token = security.create_access_token(
        {"sub": "user-123"}, expires_delta=timedelta(seconds=-1)
    )

    with pytest.raises(HTTPException):
        security.decode_access_token(expired_token)
