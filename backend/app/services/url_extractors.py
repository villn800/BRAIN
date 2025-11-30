from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .. import models
from .metadata_service import MetadataResult


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
    image = _get_meta(soup, "og:image") or _get_meta(soup, "twitter:image")
    timestamp = _get_meta(soup, "article:published_time")
    metadata = MetadataResult(url=url)
    metadata.item_type = models.ItemType.tweet
    metadata.title = tweet_text or author
    metadata.description = tweet_text or author
    metadata.image_url = image
    metadata.extra = {
        "author": author,
        "timestamp": timestamp,
    }
    return metadata


def _extract_pinterest(url: str, html: str | None) -> MetadataResult | None:
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    title = _get_meta(soup, "og:title")
    description = _get_meta(soup, "og:description")
    image = _get_meta(soup, "og:image")

    if not any([title, description, image]):
        return None

    metadata = MetadataResult(url=url)
    metadata.item_type = models.ItemType.pin
    metadata.title = title
    metadata.description = description
    metadata.image_url = image
    return metadata


def _get_meta(soup: BeautifulSoup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"property": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None