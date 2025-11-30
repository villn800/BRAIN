from __future__ import annotations

from app.core import security

LOGIN_PAYLOAD = {
    "email": "login@example.com",
    "username": "loginuser",
    "password": "SecretPass!234",
}


def _bootstrap_user(client) -> None:
    response = client.post("/api/auth/bootstrap", json=LOGIN_PAYLOAD)
    assert response.status_code == 201


def test_login_unknown_user_returns_401(app_client_factory) -> None:
    client, _ = app_client_factory()

    response = client.post(
        "/api/auth/login",
        json={"identifier": LOGIN_PAYLOAD["email"], "password": LOGIN_PAYLOAD["password"]},
    )
    assert response.status_code == 401


def test_login_wrong_password_returns_401(app_client_factory) -> None:
    client, _ = app_client_factory()
    _bootstrap_user(client)

    response = client.post(
        "/api/auth/login",
        json={"identifier": LOGIN_PAYLOAD["email"], "password": "nope-nope"},
    )
    assert response.status_code == 401


def test_login_accepts_email_and_username(app_client_factory) -> None:
    client, _ = app_client_factory()
    _bootstrap_user(client)

    email_response = client.post(
        "/api/auth/login",
        json={"identifier": LOGIN_PAYLOAD["email"], "password": LOGIN_PAYLOAD["password"]},
    )
    assert email_response.status_code == 200
    body = email_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    decoded = security.decode_access_token(body["access_token"])
    assert decoded["sub"]

    username_response = client.post(
        "/api/auth/login",
        json={"identifier": LOGIN_PAYLOAD["username"], "password": LOGIN_PAYLOAD["password"]},
    )
    assert username_response.status_code == 200
    assert username_response.json()["access_token"]
