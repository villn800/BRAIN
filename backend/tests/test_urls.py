from __future__ import annotations

import pytest

from app.core import urls


def test_normalize_url_adds_scheme_and_lowercases_domain():
    normalized = urls.normalize_url("Example.com/Test")
    assert normalized.url == "https://example.com/Test"
    assert normalized.domain == "example.com"


def test_normalize_url_strips_trailing_slash():
    normalized = urls.normalize_url("https://example.com/path/")
    assert normalized.url == "https://example.com/path"


def test_normalize_url_handles_paths_without_netloc():
    normalized = urls.normalize_url("example.org")
    assert normalized.url == "https://example.org"
    assert normalized.domain == "example.org"


def test_normalize_url_requires_host():
    with pytest.raises(ValueError):
        urls.normalize_url("http:///path-only")