from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest

from app.core.config import reset_settings
from app.services import deepseek_client


class _DummyResponse(SimpleNamespace):
    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def _setup_env(monkeypatch, base_url: str = "https://api.test") -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_API_BASE_URL", base_url)
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat-test")
    reset_settings()


def test_generate_tags_success(monkeypatch, caplog):
    _setup_env(monkeypatch)

    def _fake_post(url, headers=None, json=None, timeout=None):
        assert url == "https://api.test/chat/completions"
        assert headers["Authorization"] == "Bearer test-key"
        assert json["model"] == "deepseek-chat-test"
        content = {
            "tags": ["design", "typography", "posters"],
            "summary": "Short summary.",
            "category": "design",
        }
        payload = {"choices": [{"message": {"content": json_module.dumps(content)}}]}
        return _DummyResponse(_payload=payload)

    json_module = json
    monkeypatch.setattr(deepseek_client.httpx, "post", _fake_post)

    result = deepseek_client.generate_tags_for_text("Example tweet text", max_tags=5)

    assert result.tags == ["design", "typography", "posters"]
    assert result.summary == "Short summary."
    assert result.category == "design"
    assert "DeepSeek" not in caplog.text


def test_generate_tags_handles_http_error(monkeypatch, caplog):
    _setup_env(monkeypatch)

    def _fake_post(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(deepseek_client.httpx, "post", _fake_post)

    result = deepseek_client.generate_tags_for_text("Example tweet text")

    assert result.tags == []
    assert "Tagging unavailable" in result.summary
    assert "timeout" in caplog.text


def test_generate_tags_handles_bad_json(monkeypatch, caplog):
    _setup_env(monkeypatch)

    def _fake_post(url, headers=None, json=None, timeout=None):
        payload = {"choices": [{"message": {"content": "not-json"}}]}
        return _DummyResponse(_payload=payload)

    monkeypatch.setattr(deepseek_client.httpx, "post", _fake_post)

    result = deepseek_client.generate_tags_for_text("Example tweet text")

    assert result.tags == []
    assert "Tagging unavailable" in result.summary
    assert "not valid JSON" in caplog.text


def test_generate_tags_handles_json_code_fence(monkeypatch):
    _setup_env(monkeypatch)

    def _fake_post(url, headers=None, json=None, timeout=None):
        fenced_content = """```json
{"tags":["design"],"summary":"A design tweet.","category":"design"}
```"""
        payload = {"choices": [{"message": {"content": fenced_content}}]}
        return _DummyResponse(_payload=payload)

    monkeypatch.setattr(deepseek_client.httpx, "post", _fake_post)

    result = deepseek_client.generate_tags_for_text("Example tweet text", max_tags=4)

    assert result.tags == ["design"]
    assert result.summary == "A design tweet."
    assert result.category == "design"


def test_generate_tags_handles_non_json_text(monkeypatch, caplog):
    _setup_env(monkeypatch)

    def _fake_post(url, headers=None, json=None, timeout=None):
        payload = {"choices": [{"message": {"content": "I cannot tag this."}}]}
        return _DummyResponse(_payload=payload)

    monkeypatch.setattr(deepseek_client.httpx, "post", _fake_post)

    result = deepseek_client.generate_tags_for_text("Example tweet text")

    assert result.tags == []
    assert result.summary == "Tagging unavailable."
    assert result.category is None
    assert "not valid JSON" in caplog.text or "could not be parsed as JSON" in caplog.text
