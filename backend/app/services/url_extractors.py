from __future__ import annotations

import json
import logging
from urllib.parse import urlparse
from typing import Iterable, List, Tuple

from bs4 import BeautifulSoup

from .. import models
from ..core.config import get_settings
from .metadata_service import MetadataResult
from .twitter_headless import resolve_twitter_video_headless

logger = logging.getLogger(__name__)


def extract_for_domain(domain: str, url: str, html: str | None) -> MetadataResult | None:
    normalized = domain.lower()
    if normalized.endswith("twitter.com") or normalized.endswith("x.com"):
        return _extract_twitter(url, html)
    if normalized.endswith("pinterest.com"):
        return _extract_pinterest(url, html)
    return None


def _extract_twitter(url: str, html: str | None) -> MetadataResult | None:
    parsed = urlparse(url)
    if "/status/" not in parsed.path:
        return None
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    tweet_text = _get_meta(soup, "og:description") or _get_meta(soup, "twitter:description")
    author = _get_meta(soup, "og:title") or _get_meta(soup, "twitter:title")
    timestamp = _get_meta(soup, "article:published_time")
    metadata = MetadataResult(url=url)
    metadata.item_type = models.ItemType.tweet
    metadata.title = tweet_text or author
    metadata.description = tweet_text or author
    video_candidates = _gather_twitter_videos(soup)
    mp4_candidates, hls_candidates = _categorize_video_candidates(video_candidates)
    candidates = _gather_twitter_images(soup)
    avatar = _first_avatar(candidates)
    chosen = _pick_best_image(candidates)
    metadata.image_url = chosen
    metadata.extra = {
        "author": author,
        "timestamp": timestamp,
    }
    video_url, video_type = _pick_best_video(video_candidates)
    if video_url:
        metadata.extra["media_kind"] = "video"
        metadata.extra["video_url"] = video_url
        if video_type:
            metadata.extra["video_type"] = video_type
    else:
        metadata.extra["media_kind"] = "image"
        if hls_candidates:
            metadata.extra["twitter_hls_only"] = True
            logger.info(
                "Twitter extractor observed HLS-only candidates for %s", url
            )
    if avatar:
        metadata.extra["avatar_url"] = avatar
    if chosen is None:
        try:
            from . import metadata_service  # local import to avoid cycle
        except Exception:  # pragma: no cover - defensive
            metadata_service = None
        if metadata_service:
            fallback = metadata_service.parse_generic_metadata(url, html)
            metadata.image_url = fallback.image_url or metadata.image_url
            metadata.title = metadata.title or fallback.title
            metadata.description = metadata.description or fallback.description
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Twitter extractor candidates=%d chosen=%s avatar=%s",
            len(candidates),
            chosen,
            avatar,
        )
    settings = get_settings()
    should_try_headless = (
        settings.TWITTER_HEADLESS_ENABLED
        and "/status/" in parsed.path
        and not metadata.extra.get("video_url")
    )
    if should_try_headless:
        try:
            result = resolve_twitter_video_headless(
                url,
                timeout=settings.TWITTER_HEADLESS_TIMEOUT_SECS,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Headless Twitter resolver failed for %s: %s", url, exc)
            result = None
        if result and result.get("video_url"):
            metadata.extra["media_kind"] = "video"
            metadata.extra["video_url"] = result["video_url"]
            metadata.extra["video_type"] = result.get("video_type") or "mp4"
            if not metadata.image_url and result.get("poster_url"):
                metadata.image_url = result["poster_url"]
            metadata.extra.pop("twitter_hls_only", None)
            logger.info("Headless Twitter resolver attached video for %s", url)
        elif result and result.get("twitter_hls_only"):
            metadata.extra["twitter_hls_only"] = True
            logger.info("Headless Twitter resolver observed HLS-only for %s", url)
        else:
            logger.info("Headless Twitter resolver found no video for %s", url)
    return metadata


def _extract_pinterest(url: str, html: str | None) -> MetadataResult | None:
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    gate = _looks_like_pinterest_gate(soup)
    title = _get_meta(soup, "og:title") or _get_meta(soup, "twitter:title")
    description = _get_meta(soup, "og:description") or _get_meta(soup, "twitter:description")
    image = (
        _get_meta(soup, "og:image")
        or _get_meta(soup, "og:image:src")
        or _get_meta(soup, "twitter:image")
    )

    if any([title, description, image]):
        metadata = MetadataResult(url=url)
        metadata.item_type = models.ItemType.pin
        metadata.title = title
        metadata.description = description
        metadata.image_url = image
        try:
            from . import metadata_service  # local import to avoid cycle
        except Exception:  # pragma: no cover - defensive
            metadata_service = None
        if metadata_service and (metadata.title is None or metadata.description is None):
            generic = metadata_service.parse_generic_metadata(url, html)
            metadata.title = metadata.title or generic.title
            metadata.description = metadata.description or generic.description
            metadata.image_url = metadata.image_url or generic.image_url
        if gate:
            metadata.extra["pinterest_gate"] = True
        return metadata

    try:
        from . import metadata_service  # local import to avoid cycle
    except Exception:  # pragma: no cover - defensive
        metadata_service = None

    if metadata_service:
        generic = metadata_service.parse_generic_metadata(url, html)
        if gate:
            generic.extra["pinterest_gate"] = True
            return generic
        if any([generic.title, generic.description, generic.image_url]):
            generic.item_type = models.ItemType.pin
            return generic

    return None


def _get_meta(soup: BeautifulSoup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"property": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def _looks_like_pinterest_gate(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ", strip=True).lower()
    if not text:
        return False
    signals = (
        "log in to see",
        "sign up to continue",
        "consent",
        "login to see more",
        "sign up to see more",
        "pinterest helps you find ideas to try",
    )
    return any(signal in text for signal in signals)


def _gather_twitter_images(soup: BeautifulSoup) -> List[str]:
    """Collect all candidate images from OG/twitter meta tags and JSON-LD."""
    candidates: List[str] = []
    seen: set[str] = set()

    def _add(url: str | None) -> None:
        if not url or not _looks_like_image(url):
            return
        if url in seen:
            return
        seen.add(url)
        candidates.append(url)

    for tag in soup.find_all("meta", attrs={"property": "og:image"}):
        _add(tag.get("content"))
    for tag in soup.find_all("meta", attrs={"name": "twitter:image"}):
        _add(tag.get("content"))
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.text
        for image_url in _parse_json_ld_images(raw):
            _add(image_url)

    return candidates


def _gather_twitter_videos(soup: BeautifulSoup) -> List[Tuple[str, str | None]]:
    """Collect candidate video URLs with optional type hints."""
    candidates: List[Tuple[str, str | None]] = []
    seen: set[str] = set()

    def _add(url: str | None, type_hint: str | None) -> None:
        if not url:
            return
        if url in seen:
            return
        seen.add(url)
        candidates.append((url, type_hint))

    for tag in soup.find_all("meta", attrs={"property": "og:video"}):
        _add(tag.get("content"), None)
    for tag in soup.find_all("meta", attrs={"property": "og:video:secure_url"}):
        _add(tag.get("content"), None)
    for tag in soup.find_all("meta", attrs={"name": "twitter:player:stream"}):
        _add(tag.get("content"), None)

    # Type hints
    og_video_type = _get_meta(soup, "og:video:type")
    twitter_stream_type = _get_meta(soup, "twitter:player:stream:content_type")
    if candidates:
        # Attach type hints to existing candidates when present.
        updated: List[Tuple[str, str | None]] = []
        for url, existing in candidates:
            hint = existing or og_video_type or twitter_stream_type
            updated.append((url, hint))
        candidates = updated

    return candidates


def _parse_json_ld_images(payload: str | None) -> Iterable[str]:
    if not payload:
        return []
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []

    def _iter_images(node) -> Iterable[str]:
        if isinstance(node, str):
            yield node
        elif isinstance(node, dict):
            image_val = node.get("image") or node.get("thumbnailUrl") or node.get("url")
            if image_val:
                yield from _iter_images(image_val)
        elif isinstance(node, list):
            for item in node:
                yield from _iter_images(item)

    return _iter_images(data)


def _is_avatar(url: str) -> bool:
    lowered = url.lower()
    return "/profile_images/" in lowered or "default_profile" in lowered


def _has_media_hint(url: str) -> bool:
    lowered = url.lower()
    return (
        "/media/" in lowered
        or "card_img" in lowered
        or "twimg.com/media" in lowered
    )


def _looks_like_image(url: str) -> bool:
    lowered = url.lower()
    if not lowered.startswith(("http://", "https://")):
        return False
    if any(
        lowered.endswith(ext)
        for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif")
    ):
        return True
    return (
        "/media/" in lowered
        or "/profile_images/" in lowered
        or "card_img" in lowered
        or "twimg.com" in lowered
    )


def _pick_best_image(candidates: List[str]) -> str | None:
    if not candidates:
        return None
    media_candidates = [url for url in candidates if _has_media_hint(url) and not _is_avatar(url)]
    if media_candidates:
        return media_candidates[0]
    non_avatar = [url for url in candidates if not _is_avatar(url)]
    if non_avatar:
        return non_avatar[0]
    return candidates[0]


def _pick_best_video(candidates: List[Tuple[str, str | None]]) -> Tuple[str | None, str | None]:
    if not candidates:
        return None, None

    for url, type_hint in candidates:
        if _is_mp4(url, type_hint):
            return url, "mp4"

    # If no MP4 found, we decline to return HLS-only URLs for v1.
    return None, None


def _first_avatar(candidates: List[str]) -> str | None:
    for url in candidates:
        if _is_avatar(url):
            return url
    return None


def _is_mp4(url: str, type_hint: str | None) -> bool:
    lowered = url.lower()
    parsed = urlparse(lowered)
    if parsed.scheme in ("http", "https") and parsed.path.endswith(".mp4"):
        return True
    if parsed.scheme in ("http", "https") and ".mp4" in parsed.path:
        return True
    if type_hint and "mp4" in type_hint.lower():
        return True
    return False


def _is_hls(url: str, type_hint: str | None) -> bool:
    lowered = url.lower()
    parsed = urlparse(lowered)
    if parsed.scheme in ("http", "https") and ".m3u8" in parsed.path:
        return True
    if type_hint and ("m3u8" in type_hint.lower() or "mpegurl" in type_hint.lower()):
        return True
    return False


def _categorize_video_candidates(
    candidates: List[Tuple[str, str | None]]
) -> tuple[list[Tuple[str, str | None]], list[Tuple[str, str | None]]]:
    mp4_candidates: list[Tuple[str, str | None]] = []
    hls_candidates: list[Tuple[str, str | None]] = []
    for url, type_hint in candidates:
        if _is_mp4(url, type_hint):
            mp4_candidates.append((url, type_hint))
        elif _is_hls(url, type_hint):
            hls_candidates.append((url, type_hint))
    return mp4_candidates, hls_candidates
