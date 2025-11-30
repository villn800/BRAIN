from __future__ import annotations

from types import SimpleNamespace

import httpx

from app.services import metadata_service


class _StubResponse(SimpleNamespace):
    def __init__(self, *, text: str = "", status_code: int = 200):
        super().__init__(text=text, status_code=status_code)


def test_fetch_html_returns_error_for_http_failure():
    result = metadata_service.fetch_html(
        "https://example.com",
        http_get=lambda *args, **kwargs: _StubResponse(text="", status_code=500),
    )
    assert result.error == "HTTP 500"
    assert result.html is None


def test_parse_generic_metadata_extracts_tags():
    html = """
    <html>
      <head>
        <title>Example Title</title>
        <meta name='description' content='Summary here'>
        <meta property='og:image' content='https://cdn/img.jpg'>
      </head>
    </html>
    """
    metadata = metadata_service.parse_generic_metadata("https://example.com", html)
    assert metadata.title == "Example Title"
    assert metadata.description == "Summary here"
    assert metadata.image_url == "https://cdn/img.jpg"


def test_fetch_metadata_sets_error_on_exception():
    def _raiser(*args, **kwargs):
        raise httpx.ConnectTimeout("boom")

    metadata = metadata_service.fetch_metadata(
        "https://timeout.test",
        http_get=_raiser,
    )
    assert metadata.error is not None