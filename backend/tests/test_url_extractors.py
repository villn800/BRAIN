from __future__ import annotations

from pathlib import Path

from app import models
from app.services import url_extractors

FIXTURES = Path(__file__).parent / "fixtures"
TWITTER_FIXTURES = FIXTURES / "twitter"
PINTEREST_FIXTURES = FIXTURES / "pinterest"


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
    html = (TWITTER_FIXTURES / "quote_tweet_with_media_juniorkingpp.html").read_text()
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
    html = (TWITTER_FIXTURES / "quote_tweet_or_card_girlflours.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "twitter.com",
        "https://twitter.com/girlflours/status/1996331045344735356",
        html,
    )
    assert metadata is not None
    assert metadata.image_url and "/media/" in metadata.image_url
    assert metadata.extra.get("avatar_url") is None


def test_twitter_extractor_simple_image_tweet():
    html = (TWITTER_FIXTURES / "simple_image_tweet.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "twitter.com",
        "https://twitter.com/Interior/status/463440424141459456",
        html,
    )
    assert metadata is not None
    assert metadata.image_url and "/media/" in metadata.image_url


def test_twitter_extractor_text_only_falls_back_to_avatar():
    html = (TWITTER_FIXTURES / "text_only_tweet.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "x.com",
        "https://x.com/jack/status/20",
        html,
    )
    assert metadata is not None
    assert metadata.image_url and "/profile_images/" in metadata.image_url
    assert metadata.extra.get("avatar_url") == metadata.image_url


def test_twitter_video_detection():
    html = (TWITTER_FIXTURES / "video_simple.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "twitter.com",
        "https://twitter.com/user/status/555",
        html,
    )
    assert metadata is not None
    assert metadata.extra.get("media_kind") == "video"
    assert metadata.extra.get("video_url", "").endswith(".mp4")
    assert metadata.extra.get("video_type") == "mp4"
    assert not metadata.extra.get("twitter_hls_only")
    assert metadata.item_type == models.ItemType.tweet
    assert metadata.image_url  # poster retained


def test_twitter_video_detection_with_query_string():
    candidates = [
        (
            "https://video.twimg.com/ext_tw_video/1842312345678901234/pu/vid/720x720/abcdEFGH.mp4?tag=21",
            None,
        ),
        ("https://video.twimg.com/segment_only.m3u8?tag=21", None),
    ]

    url, video_type = url_extractors._pick_best_video(candidates)
    assert url.endswith(".mp4?tag=21")
    assert video_type == "mp4"


def test_twitter_hls_fallback_to_image():
    html = (TWITTER_FIXTURES / "video_hls.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "x.com",
        "https://x.com/user/status/777",
        html,
    )
    assert metadata is not None
    assert metadata.extra.get("media_kind") == "image"
    assert metadata.extra.get("video_url") is None
    assert metadata.extra.get("twitter_hls_only") is True
    assert metadata.image_url and metadata.image_url.endswith("hls_poster.jpg")


def test_twitter_headless_runs_when_flag_enabled(monkeypatch):
    html = """
    <html>
      <head>
        <meta property='og:description' content='Tweet text here'>
        <meta property='og:title' content='Author Name (@handle)'>
      </head>
    </html>
    """

    class FakeSettings:
        TWITTER_HEADLESS_ENABLED = True
        TWITTER_HEADLESS_TIMEOUT_SECS = 1.0

    captured = {}

    def _fake_resolver(url: str, timeout: float = 0.0):
        captured["called"] = (url, timeout)
        return {
            "video_url": "https://video.example/video.mp4",
            "video_type": "mp4",
            "poster_url": "https://pbs.twimg.com/media/poster.jpg",
        }

    monkeypatch.setattr(url_extractors, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(url_extractors, "resolve_twitter_video_headless", _fake_resolver)

    metadata = url_extractors.extract_for_domain(
        "twitter.com",
        "https://twitter.com/user/status/123456",
        html,
    )
    assert captured["called"][0].endswith("/123456")
    assert metadata.extra["media_kind"] == "video"
    assert metadata.extra["video_url"] == "https://video.example/video.mp4"
    assert metadata.extra["video_type"] == "mp4"
    assert metadata.image_url == "https://pbs.twimg.com/media/poster.jpg"


def test_twitter_headless_skipped_when_flag_disabled(monkeypatch):
    html = """
    <html>
      <head>
        <meta property='og:description' content='Tweet text here'>
        <meta property='og:title' content='Author Name (@handle)'>
      </head>
    </html>
    """

    class FakeSettings:
        TWITTER_HEADLESS_ENABLED = False
        TWITTER_HEADLESS_TIMEOUT_SECS = 1.0

    def _fail_resolver(*_args, **_kwargs):
        raise AssertionError("headless resolver should not be called")

    monkeypatch.setattr(url_extractors, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(url_extractors, "resolve_twitter_video_headless", _fail_resolver)

    metadata = url_extractors.extract_for_domain(
        "x.com",
        "https://x.com/user/status/123456",
        html,
    )
    assert metadata.extra.get("video_url") is None
    assert metadata.extra.get("media_kind") == "image"


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


def test_pinterest_real_pin_uses_og_or_twitter_meta():
    html = (PINTEREST_FIXTURES / "real_pin.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "pinterest.com",
        "https://www.pinterest.com/pin/10062799163935716/",
        html,
    )
    assert metadata is not None
    assert metadata.item_type == models.ItemType.pin
    assert metadata.title
    assert metadata.description
    assert metadata.image_url and metadata.image_url.startswith("https://i.pinimg.com/")


def test_pinterest_gate_page_detected_and_flagged():
    html = (PINTEREST_FIXTURES / "gate_page.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "pinterest.com",
        "https://www.pinterest.com/pin/gate/",
        html,
    )
    assert metadata is not None
    assert metadata.item_type == models.ItemType.url
    assert metadata.extra.get("pinterest_gate") is True
    assert metadata.title == "Pinterest"
    assert metadata.image_url is None


def test_pinterest_falls_back_to_pin_when_generic_meta_exists():
    html = (PINTEREST_FIXTURES / "generic_meta.html").read_text()
    metadata = url_extractors.extract_for_domain(
        "pinterest.com",
        "https://www.pinterest.com/pin/board/",
        html,
    )
    assert metadata is not None
    assert metadata.item_type == models.ItemType.pin
    assert metadata.title == "Pinterest Ideas Board"
    assert metadata.image_url.endswith("pinterest-board.jpg")


def test_extractor_returns_none_for_unmatched_domain():
    assert (
        url_extractors.extract_for_domain(
            "example.com",
            "https://example.com/page",
            "<html></html>",
        )
        is None
    )
