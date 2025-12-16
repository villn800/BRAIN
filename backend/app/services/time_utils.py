from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

TWITTER_EPOCH_MS = 1288834974657  # 2010-11-04 01:42:54.657 UTC


def parse_metadata_timestamp(value: object | None) -> Optional[datetime]:
    """Best-effort parsing for timestamps coming from scraped metadata.

    Handles ISO-8601 strings (with or without trailing Z), common
    RFC2822-style dates, and the "Month day, Year" format returned by
    Twitter/X embeds (e.g., "June 5, 2011"). Returns an aware UTC datetime
    or None when parsing fails.
    """
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Normalize trailing Z for ISO parsing.
    iso_candidates = [text]
    if text.endswith("Z"):
        iso_candidates.insert(0, f"{text[:-1]}+00:00")

    for candidate in iso_candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        parsed = None

    if parsed:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return None


def parse_twitter_snowflake_timestamp(value: str | int | None) -> Optional[datetime]:
    """Decode a Twitter/X snowflake ID into a UTC datetime."""
    if value is None:
        return None
    try:
        snowflake = int(str(value))
        timestamp_ms = (snowflake >> 22) + TWITTER_EPOCH_MS
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    except (ValueError, OverflowError):
        return None


def parse_twitter_timestamp_from_url(url: str | None) -> Optional[datetime]:
    """Extract a tweet ID from the URL and decode it to a UTC datetime."""
    if not url:
        return None
    try:
        from . import url_extractors  # local import to avoid cycle
    except Exception:
        url_extractors = None
    if not url_extractors:
        return None
    tweet_id = url_extractors._parse_tweet_id(url)  # noqa: SLF001 - internal helper reuse
    if not tweet_id:
        return None
    return parse_twitter_snowflake_timestamp(tweet_id)
