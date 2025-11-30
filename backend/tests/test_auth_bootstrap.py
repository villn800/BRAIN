from __future__ import annotations

from app import database, models


BOOTSTRAP_PAYLOAD = {
    "email": "admin@example.com",
    "username": "admin",
    "password": "StrongPass!123",
}


def test_bootstrap_creates_initial_admin(app_client_factory) -> None:
    client, _ = app_client_factory()

    response = client.post("/api/auth/bootstrap", json=BOOTSTRAP_PAYLOAD)
    assert response.status_code == 201

    payload = response.json()
    assert payload["email"] == BOOTSTRAP_PAYLOAD["email"]
    assert payload["username"] == BOOTSTRAP_PAYLOAD["username"]
    assert payload["is_admin"] is True

    session = database.SessionLocal()
    try:
        user = session.query(models.User).first()
        assert user is not None
        assert user.is_admin
        assert user.email == BOOTSTRAP_PAYLOAD["email"]
    finally:
        session.close()


def test_bootstrap_rejects_when_user_exists(app_client_factory) -> None:
    client, _ = app_client_factory()

    first = client.post("/api/auth/bootstrap", json=BOOTSTRAP_PAYLOAD)
    assert first.status_code == 201

    second = client.post(
        "/api/auth/bootstrap",
        json={**BOOTSTRAP_PAYLOAD, "email": "second@example.com", "username": "second"},
    )
    assert second.status_code == 403

    session = database.SessionLocal()
    try:
        assert session.query(models.User).count() == 1
    finally:
        session.close()
