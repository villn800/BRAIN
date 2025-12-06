from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def resolve_twitter_video_headless(
    url: str,
    *,
    timeout: float = 15.0,
) -> dict[str, str | None] | None:
    """Best-effort headless resolver for Twitter/X videos."""
    logger.info("twitter_headless_start url=%s timeout=%.1fs", url, timeout)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.info(
            "twitter_headless_skipped url=%s reason=playwright_not_installed", url
        )
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
                from urllib.parse import urlparse

                parsed = urlparse(lowered)
                path = parsed.path
                if ".mp4" in path:
                    captured.append((response_url, "mp4"))
                elif ".m3u8" in path:
                    captured.append((response_url, "hls"))

            page.on("response", handle_response)
            page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
            page.wait_for_timeout(2000)
            browser.close()

            mp4_candidates = [entry for entry in captured if entry[1] == "mp4"]
            hls_candidates = [entry for entry in captured if entry[1] == "hls"]
            if not captured:
                logger.info(
                    "twitter_headless outcome=no_media url=%s candidates=0 mp4=0 hls=0",
                    url,
                )
                return None

            if mp4_candidates:
                preferred = next(
                    (entry for entry in captured if entry[1] == "mp4"), captured[0]
                )
                logger.info(
                    "twitter_headless outcome=success url=%s candidates=%d mp4=%d hls=%d chosen_type=%s",
                    url,
                    len(captured),
                    len(mp4_candidates),
                    len(hls_candidates),
                    preferred[1],
                )
                logger.debug(
                    "twitter_headless_candidates url=%s candidates=%s",
                    url,
                    captured,
                )
                return {
                    "video_url": preferred[0],
                    "video_type": preferred[1],
                    "poster_url": None,
                }

            if hls_candidates:
                logger.info(
                    "twitter_headless outcome=hls_only url=%s candidates=%d mp4=0 hls=%d",
                    url,
                    len(captured),
                    len(hls_candidates),
                )
                logger.debug(
                    "twitter_headless_candidates url=%s candidates=%s",
                    url,
                    captured,
                )
                return {
                    "video_url": None,
                    "video_type": None,
                    "poster_url": None,
                    "twitter_hls_only": True,
                }

            logger.info(
                "twitter_headless outcome=no_media url=%s candidates=%d mp4=0 hls=0",
                url,
                len(captured),
            )
            return None
    except Exception as exc:  # pragma: no cover - defensive; exercised via tests
        logger.warning(
            "twitter_headless outcome=error url=%s reason=%s", url, exc, exc_info=True
        )
        return None
