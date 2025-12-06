from __future__ import annotations

import sys
import types

from app.services.twitter_headless import resolve_twitter_video_headless


def _install_fake_playwright(monkeypatch, responses: list[str]):
    """Provide a fake sync_playwright that replays the given response URLs."""

    class FakeResponse:
        def __init__(self, url: str):
            self.url = url

    class FakePage:
        def __init__(self, resp_urls: list[str]):
            self._handlers = []
            self._resp_urls = resp_urls

        def on(self, event: str, handler):
            if event == "response":
                self._handlers.append(handler)

        def goto(self, *_args, **_kwargs):
            for resp in self._resp_urls:
                for handler in list(self._handlers):
                    handler(FakeResponse(resp))

        def wait_for_timeout(self, *_args, **_kwargs):
            return None

    class FakeBrowser:
        def __init__(self, resp_urls: list[str]):
            self._resp_urls = resp_urls

        def new_page(self):
            return FakePage(self._resp_urls)

        def close(self):
            return None

    class FakeChromium:
        def __init__(self, resp_urls: list[str]):
            self._resp_urls = resp_urls

        def launch(self, **_kwargs):
            return FakeBrowser(self._resp_urls)

    class FakePlaywright:
        def __init__(self, resp_urls: list[str]):
            self.chromium = FakeChromium(resp_urls)

    class FakeContextManager:
        def __init__(self, resp_urls: list[str]):
            self._resp_urls = resp_urls

        def __enter__(self):
            return FakePlaywright(self._resp_urls)

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_sync_api = types.ModuleType("playwright.sync_api")
    fake_sync_api.sync_playwright = lambda: FakeContextManager(responses)
    fake_playwright = types.ModuleType("playwright")
    fake_playwright.sync_api = fake_sync_api

    monkeypatch.setitem(sys.modules, "playwright", fake_playwright)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_sync_api)


def test_resolves_mp4_when_present(monkeypatch):
    responses = [
        "https://video.twimg.com/segment1.m3u8",
        "https://video.twimg.com/clip.mp4",
    ]
    _install_fake_playwright(monkeypatch, responses)

    result = resolve_twitter_video_headless("https://x.com/user/status/1", timeout=1.0)
    assert result
    assert result["video_url"].endswith("clip.mp4")
    assert result["video_type"] == "mp4"
    assert result.get("poster_url") is None


def test_resolves_mp4_with_query(monkeypatch):
    responses = [
        "https://video.twimg.com/segment1.m3u8?tag=21",
        "https://video.twimg.com/clip.mp4?tag=21",
    ]
    _install_fake_playwright(monkeypatch, responses)

    result = resolve_twitter_video_headless("https://x.com/user/status/3", timeout=1.0)
    assert result
    assert result["video_url"].endswith("clip.mp4?tag=21")
    assert result["video_type"] == "mp4"


def test_returns_none_when_no_media(monkeypatch):
    responses: list[str] = [
        "https://video.twimg.com/not-video.txt",
        "https://pbs.twimg.com/media/image.jpg",
    ]
    _install_fake_playwright(monkeypatch, responses)

    result = resolve_twitter_video_headless("https://x.com/user/status/2", timeout=1.0)
    assert result is None
