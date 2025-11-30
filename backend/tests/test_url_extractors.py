from __future__ import annotations

from app import models
from app.services import url_extractors


def test_twitter_extractor_returns_metadata():
    html = """
    <html>
      <head>
        <meta property='og:description' content='Tweet text here'>
        <meta property='og:title' content='Author Name (@handle)'>
        <meta property='og:image' content='https://cdn/twitter.jpg'>
        <meta property='article:published_time' content='2025-11-25T12:00:00Z'>
      </head>
    </html>
    """
    metadata = url_extractors.extract_for_domain(
        "twitter.com",
        "https://twitter.com/user/status/123",
        html,
    )
    assert metadata is not None
    assert metadata.item_type == models.ItemType.tweet
    assert metadata.title == "Tweet text here"
    assert metadata.image_url == "https://cdn/twitter.jpg"
    assert metadata.extra["author"].startswith("Author")


def test_pinterest_extractor_handles_basic_meta():
    html = """
    <meta property='og:title' content='Pin Title'>
    <meta property='og:description' content='Pin Desc'>
    <meta property='og:image' content='https://cdn/pin.jpg'>
    """
    metadata = url_extractors.extract_for_domain(
        "pinterest.com",
        "https://www.pinterest.com/pin/1",
        html,
    )
    assert metadata is not None
    assert metadata.item_type == models.ItemType.pin
    assert metadata.title == "Pin Title"


def test_extractor_returns_none_for_unmatched_domain():
    assert (
        url_extractors.extract_for_domain(
            "example.com",
            "https://example.com/page",
            "<html></html>",
        )
        is None
    )