from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def resolve_twitter_video_headless(
    url: str,
    *,
    timeout: float = 15.0,
) -> dict[str, str | None] | None:
    """Best-effort headless resolver for Twitter/X videos."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.info("Playwright not installed — skipping headless resolver.")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            captured: list[tuple[str, str]] = []

            def handle_response(response) -> None:
                try:
                    response_url = response.url
                except Exception:
                    return
                lowered = response_url.lower()
                if "video.twimg.com" not in lowered:
                    return
                if lowered.endswith(".mp4"):
                    captured.append((response_url, "mp4"))
                elif lowered.endswith(".m3u8"):
                    captured.append((response_url, "hls"))

            page.on("response", handle_response)
            page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
            page.wait_for_timeout(2000)
            browser.close()

            if not captured:
                logger.info("Headless Twitter resolver found no video for %s", url)
                return None

            preferred = next((entry for entry in captured if entry[1] == "mp4"), captured[0])
            return {
                "video_url": preferred[0],
                "video_type": preferred[1],
                "poster_url": None,
            }
    except Exception as exc:  # pragma: no cover - defensive; exercised via tests
        logger.warning("Headless Twitter resolver failed for %s: %s", url, exc)
        return None
