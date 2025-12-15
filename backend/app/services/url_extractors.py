from __future__ import annotations

import json
import logging
import re
from urllib.parse import urlparse
from typing import Iterable, List, Tuple

import httpx
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
    metadata.extra["primary_image_is_avatar"] = bool(avatar and chosen and avatar == chosen)
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

    # Fallback when X removed OG/Twitter meta tags or when we didn't get an image.
    if (not metadata.title and not metadata.description) or not _looks_like_image_url(metadata.image_url):
        fallback = _twitter_oembed_fallback(url)
        if fallback:
            metadata.title = metadata.title or fallback.get("text")
            metadata.description = metadata.description or fallback.get("text")
            if not _looks_like_image_url(metadata.image_url):
                metadata.image_url = fallback.get("image_url") or metadata.image_url
            if fallback.get("author") and not metadata.extra.get("author"):
                metadata.extra["author"] = fallback["author"]
            if fallback.get("timestamp") and not metadata.extra.get("timestamp"):
                metadata.extra["timestamp"] = fallback["timestamp"]
            if metadata.extra.get("media_kind") is None:
                metadata.extra["media_kind"] = "image"
    return metadata


def _twitter_oembed_fallback(url: str) -> dict[str, str | None] | None:
    """Best-effort metadata recovery for X/Twitter when OG meta tags are absent."""
    tweet_id = _parse_tweet_id(url)
    vx_data = _twitter_vx_lookup(tweet_id) if tweet_id else None
    vx_text = vx_data.get("text") if vx_data else None
    vx_image = vx_data.get("image_url") if vx_data else None
    vx_author = vx_data.get("author") if vx_data else None
    vx_timestamp = vx_data.get("timestamp") if vx_data else None

    try:
        resp = httpx.get(
            "https://publish.twitter.com/oembed",
            params={"url": url},
            timeout=6.0,
            follow_redirects=True,
        )
        if resp.status_code >= 400:
            return None
        payload = resp.json()
    except Exception:  # pragma: no cover - defensive
        payload = {}

    html = payload.get("html") or ""
    soup = BeautifulSoup(html, "html.parser")
    text_node = soup.find("p")
    text = vx_text or (text_node.get_text(" ", strip=True) if text_node else None)
    image_url = vx_image or _resolve_tco_image(soup)
    if vx_author:
        payload.setdefault("author_name", vx_author)
    if vx_timestamp:
        payload.setdefault("timestamp", vx_timestamp)
    timestamp = None
    # The last <a> in the embed usually contains the timestamp label.
    links = soup.find_all("a")
    if links:
        timestamp = links[-1].get_text(" ", strip=True) or None

    return {
        "text": text,
        "author": payload.get("author_name"),
        "image_url": image_url,
        "timestamp": timestamp,
    }


def _parse_tweet_id(url: str) -> str | None:
    parsed = urlparse(url)
    match = re.search(r"/status/(\d+)", parsed.path)
    return match.group(1) if match else None


def _twitter_vx_lookup(tweet_id: str) -> dict[str, str | None] | None:
    """Use the public vxtwitter API as a resilience fallback to grab media/text."""
    try:
        resp = httpx.get(f"https://api.vxtwitter.com/status/{tweet_id}", timeout=6.0)
        if resp.status_code >= 400:
            return None
        data = resp.json()
    except Exception:  # pragma: no cover - defensive
        return None

    text = data.get("text")
    author = data.get("user_name") or data.get("user_screen_name")
    timestamp = data.get("date")
    image_url = None
    media = data.get("media_extended") or []
    qrt_media = (data.get("qrt") or {}).get("media_extended") or []
    chosen_media = media or qrt_media
    if chosen_media:
        first = chosen_media[0] or {}
        image_url = first.get("url") or first.get("thumbnail_url")

    return {
        "text": text,
        "author": author,
        "timestamp": timestamp,
        "image_url": image_url,
    }


def _resolve_tco_image(soup: BeautifulSoup) -> str | None:
    """Follow pic.twitter.com/t.co links from the embed to the underlying media URL."""
    target = None
    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if href and ("pic.twitter.com" in href or "t.co/" in href):
            target = href
            break
    if not target:
        return None

    try:
        response = httpx.get(target, timeout=6.0, follow_redirects=True)
    except Exception:  # pragma: no cover - defensive
        return None

    final_url = str(response.url)
    content_type = response.headers.get("content-type", "")
    if final_url and content_type.startswith("image/"):
        return final_url

    # If we landed on a Twitter photo page, try to scrape its og:image.
    if final_url and "twitter.com" in final_url and "/photo/" in final_url:
        try:
            html = response.text
            from . import metadata_service  # local import to avoid cycle
            parsed = metadata_service.parse_generic_metadata(final_url, html)
            if parsed.image_url:
                return parsed.image_url
        except Exception:  # pragma: no cover - defensive
            return final_url or None

    return final_url or None
    return None


def _looks_like_image_url(url: str | None) -> bool:
    if not url:
        return False
    lower = url.lower()
    if "pbs.twimg.com" in lower:
        return True
    if any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return True
    return False


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
