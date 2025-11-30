from __future__ import annotations

from datetime import timedelta

from app import database, models
from app.core import security

USER_FIXTURE = {
    "email": "guard@example.com",
    "username": "guarduser",
    "password": "GuardPass!789",
}


def _bootstrap_and_login(client) -> tuple[str, models.User]:
    response = client.post("/api/auth/bootstrap", json=USER_FIXTURE)
    assert response.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"identifier": USER_FIXTURE["email"], "password": USER_FIXTURE["password"]},
    )
    assert login.status_code == 200

    session = database.SessionLocal()
    try:
        user = session.query(models.User).first()
    finally:
        session.close()
    return login.json()["access_token"], user


def _seed_item(user: models.User) -> None:
    session = database.SessionLocal()
    try:
        item = models.Item(user_id=user.id, title="Guarded Item", type=models.ItemType.url)
        session.add(item)
        session.commit()
    finally:
        session.close()


def test_items_requires_token(app_client_factory) -> None:
    client, _ = app_client_factory()
    response = client.get("/api/items/")
    assert response.status_code == 401


def test_items_rejects_invalid_or_expired_token(app_client_factory) -> None:
    client, _ = app_client_factory()
    token, user = _bootstrap_and_login(client)

    # Invalid token
    response = client.get(
        "/api/items/",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401

    # Expired token
    expired_token = security.create_access_token(
        {"sub": str(user.id)}, expires_delta=timedelta(seconds=-1)
    )
    expired_response = client.get(
        "/api/items/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert expired_response.status_code == 401


def test_items_returns_data_with_valid_token(app_client_factory) -> None:
    client, _ = app_client_factory()
    token, user = _bootstrap_and_login(client)
    _seed_item(user)

    response = client.get(
        "/api/items/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["title"] == "Guarded Item"
