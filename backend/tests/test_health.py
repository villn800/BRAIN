from __future__ import annotations

from datetime import datetime

from app.database import get_db


def test_health_endpoint_reports_ok(app_client_factory):
    client, _ = app_client_factory()

    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["db"] == "ok"
    assert payload["storage"] == "ok"
    _assert_diagnostics(payload)


def test_health_reports_storage_missing(app_client_factory):
    client, storage_dir = app_client_factory(storage_exists=False)

    assert not storage_dir.exists()

    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["storage"] == "missing"
    assert payload["db"] == "ok"
    _assert_diagnostics(payload)


def test_health_reports_db_error(app_client_factory):
    client, _ = app_client_factory()

    class BrokenSession:
        def execute(self, *_args, **_kwargs):  # pragma: no cover - simple stub
            raise RuntimeError("db down")

    def broken_db_dep():
        return BrokenSession()

    client.app.dependency_overrides[get_db] = broken_db_dep

    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["db"] == "error"
    assert payload["status"] == "degraded"
    _assert_diagnostics(payload)

    client.app.dependency_overrides.clear()


def _assert_diagnostics(payload):
    assert payload["environment"]
    assert payload["version"]
    assert payload["timestamp"]
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))