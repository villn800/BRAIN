from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from .. import models

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 "
        "BRAIN-MetadataFetcher/1.0"
    )
}
DEFAULT_TIMEOUT = 8.0
logger = logging.getLogger(__name__)

HttpGetter = Callable[..., httpx.Response]


@dataclass
class HtmlFetchResult:
    html: str | None
    error: str | None = None
    status_code: int | None = None


@dataclass
class MetadataResult:
    url: str
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    text_content: str | None = None
    item_type: models.ItemType = models.ItemType.url
    error: str | None = None
    raw_html: str | None = None
    extra: dict[str, str | None] = field(default_factory=dict)


def fetch_html(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    http_get: HttpGetter | None = None,
) -> HtmlFetchResult:
    getter = http_get or httpx.get
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    domain = urlparse(url).netloc.lower()
    is_pinterest = "pinterest.com" in domain
    try:
        # Always follow redirects so we can see the final page metadata (Pinterest pins often 301).
        response = getter(url, timeout=timeout, headers=merged_headers, follow_redirects=True)
    except httpx.HTTPError as exc:  # pragma: no cover - network errors handled in tests
        response_obj = getattr(exc, "response", None)
        status_code = getattr(response_obj, "status_code", None)
        if is_pinterest:
            logger.info(
                "pinterest_fetch url=%s status=%s error=%s",
                url,
                status_code,
                str(exc),
            )
        return HtmlFetchResult(html=None, error=str(exc), status_code=status_code)

    status = getattr(response, "status_code", None)
    if status is not None and status >= 400:
        text = getattr(response, "text", "") or ""
        if is_pinterest:
            logger.info(
                "pinterest_fetch url=%s status=%s content_length=%s prefix=%s",
                url,
                status,
                len(text),
                " ".join(text[:200].split()),
            )
        return HtmlFetchResult(html=None, error=f"HTTP {status}", status_code=status)

    text = getattr(response, "text", None)
    if is_pinterest:
        preview = ""
        if text:
            preview = " ".join(text[:200].split())
        logger.info(
            "pinterest_fetch url=%s status=%s content_length=%s prefix=%s",
            url,
            status,
            len(text or ""),
            preview,
        )
    return HtmlFetchResult(html=text or "", status_code=status)


def parse_generic_metadata(url: str, html: str | None) -> MetadataResult:
    metadata = MetadataResult(url=url)
    if not html:
        metadata.error = "Empty response"
        metadata.raw_html = html
        return metadata

    soup = BeautifulSoup(html, "html.parser")
    metadata.title = _first_nonempty(
        soup.find("meta", attrs={"property": "og:title"}),
        soup.find("title"),
        soup.find("meta", attrs={"name": "twitter:title"}),
    )
    metadata.description = _first_nonempty(
        soup.find("meta", attrs={"property": "og:description"}),
        soup.find("meta", attrs={"name": "description"}),
        soup.find("meta", attrs={"name": "twitter:description"}),
    )
    metadata.image_url = _first_nonempty(
        soup.find("meta", attrs={"property": "og:image"}),
        soup.find("meta", attrs={"name": "twitter:image"}),
    )
    metadata.raw_html = html
    metadata.item_type = models.ItemType.url
    return metadata


def fetch_metadata(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    http_get: HttpGetter | None = None,
) -> MetadataResult:
    fetch_result = fetch_html(url, timeout=timeout, headers=headers, http_get=http_get)
    metadata = parse_generic_metadata(url, fetch_result.html)
    metadata.error = fetch_result.error
    metadata.raw_html = fetch_result.html
    return metadata


def _first_nonempty(*elements) -> str | None:
    for element in elements:
        if element is None:
            continue
        if hasattr(element, "get"):
            content = element.get("content")
            if content:
                return content.strip()
        text = getattr(element, "text", None)
        if text:
            stripped = text.strip()
            if stripped:
                return stripped
    return None
