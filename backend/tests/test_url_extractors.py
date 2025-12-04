from __future__ import annotations

from pathlib import Path

from app import models
from app.services import url_extractors

FIXTURES = Path(__file__).parent / "fixtures" / "twitter"


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


def test_twitter_extractor_prefers_media_over_avatar_with_json_ld():
    html = (FIXTURES / "quote_tweet_with_media_juniorkingpp.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "x.com",
        "https://x.com/juniorkingpp/status/1996087779269464125",
        html,
    )
    assert metadata is not None
    assert metadata.image_url
    assert "/media/" in metadata.image_url
    assert metadata.extra.get("avatar_url")
    assert "/profile_images/" in metadata.extra["avatar_url"]


def test_twitter_extractor_handles_card_image_meta():
    html = (FIXTURES / "quote_tweet_or_card_girlflours.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "twitter.com",
        "https://twitter.com/girlflours/status/1996331045344735356",
        html,
    )
    assert metadata is not None
    assert metadata.image_url and "/media/" in metadata.image_url
    assert metadata.extra.get("avatar_url") is None


def test_twitter_extractor_simple_image_tweet():
    html = (FIXTURES / "simple_image_tweet.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "twitter.com",
        "https://twitter.com/Interior/status/463440424141459456",
        html,
    )
    assert metadata is not None
    assert metadata.image_url and "/media/" in metadata.image_url


def test_twitter_extractor_text_only_falls_back_to_avatar():
    html = (FIXTURES / "text_only_tweet.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "x.com",
        "https://x.com/jack/status/20",
        html,
    )
    assert metadata is not None
    assert metadata.image_url and "/profile_images/" in metadata.image_url
    assert metadata.extra.get("avatar_url") == metadata.image_url


def test_twitter_video_detection():
    html = (FIXTURES / "video_simple.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "twitter.com",
        "https://twitter.com/user/status/555",
        html,
    )
    assert metadata is not None
    assert metadata.extra.get("media_kind") == "video"
    assert metadata.extra.get("video_url", "").endswith(".mp4")
    assert metadata.extra.get("video_type") == "mp4"
    assert metadata.item_type == models.ItemType.tweet
    assert metadata.image_url  # poster retained


def test_twitter_hls_fallback_to_image():
    html = (FIXTURES / "video_hls.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "x.com",
        "https://x.com/user/status/777",
        html,
    )
    assert metadata is not None
    assert metadata.extra.get("media_kind") == "image"
    assert metadata.extra.get("video_url") is None
    assert metadata.image_url and metadata.image_url.endswith("hls_poster.jpg")


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
