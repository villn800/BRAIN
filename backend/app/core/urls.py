from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from urllib.parse import urlparse, urlunparse

DEFAULT_SCHEME = "https"


@dataclass(frozen=True)
class NormalizedURL:
    url: str
    domain: str


def normalize_url(raw: str) -> NormalizedURL:
    """Normalize a raw URL and derive its origin domain."""
    if raw is None:
        raise ValueError("URL is required")

    candidate = raw.strip()
    if not candidate:
        raise ValueError("URL is required")

    if "//" not in candidate:
        candidate = f"{DEFAULT_SCHEME}://{candidate}"

    parsed = urlparse(candidate)
    scheme = parsed.scheme.lower() or DEFAULT_SCHEME
    netloc = parsed.netloc.lower()

    if not netloc:
        # Handle inputs like "example.com" where urlparse dumps into path
        netloc = parsed.path.lower()
        path = ""
        query = parsed.query
        fragment = parsed.fragment
    else:
        path = parsed.path
        query = parsed.query
        fragment = parsed.fragment

    if not netloc or netloc.startswith("/"):
        raise ValueError("Invalid URL: missing host")

    normalized_path = path.rstrip("/") or ("/" if path else "")

    normalized = urlunparse(
        (
            scheme,
            netloc,
            normalized_path,
            "",
            query,
            fragment,
        )
    )

    return NormalizedURL(url=normalized, domain=netloc)