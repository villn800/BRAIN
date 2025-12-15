"""
Backfill script to set extra.primary_image_is_avatar for existing Twitter/X items.

Safe by default (dry-run). Use --apply to write changes.
"""

from __future__ import annotations

import argparse
import logging
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy import or_, select

from app import models
from app.database import SessionLocal, configure_engine
from app.services import metadata_service, url_extractors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill extra.primary_image_is_avatar for Twitter/X items"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of items to scan (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the run without writing changes (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes (must be set to write updates)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    args = parser.parse_args()
    if not args.apply:
        args.dry_run = True
    return args


def _is_twitter_item(item: models.Item) -> bool:
    domain = (item.origin_domain or "").lower()
    if "twitter.com" in domain or "x.com" in domain:
        return True
    if item.source_url:
        parsed = urlparse(item.source_url)
        netloc = parsed.netloc.lower()
        return "twitter.com" in netloc or "x.com" in netloc
    return False


def _pick_domain(item: models.Item) -> str:
    if item.origin_domain:
        return item.origin_domain
    if item.source_url:
        return urlparse(item.source_url).netloc
    return ""


def _compute_flag(item: models.Item) -> Optional[bool]:
    if not item.source_url:
        logging.warning("Item %s missing source_url; skipping", item.id)
        return None

    html_result = metadata_service.fetch_html(item.source_url)
    if html_result.error and not html_result.html:
        logging.warning("Fetch failed for %s: %s", item.source_url, html_result.error)
        return None

    metadata = url_extractors.extract_for_domain(
        _pick_domain(item),
        item.source_url,
        html_result.html,
    )
    if not metadata:
        logging.warning("No metadata extracted for %s", item.source_url)
        return None
    return bool(metadata.extra.get("primary_image_is_avatar"))


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    configure_engine()
    session = SessionLocal()

    scanned = 0
    already_set = 0
    planned_updates = 0
    applied_updates = 0
    failures = 0

    try:
        query = select(models.Item).where(
            or_(
                models.Item.type == models.ItemType.tweet,
                models.Item.origin_domain.ilike("%twitter.com%"),
                models.Item.origin_domain.ilike("%x.com%"),
            )
        ).order_by(models.Item.created_at.desc())
        if args.limit:
            query = query.limit(args.limit)

        items = session.scalars(query).all()
        for item in items:
            scanned += 1
            if not _is_twitter_item(item):
                continue
            extra = item.extra or {}
            if extra.get("primary_image_is_avatar") is not None:
                already_set += 1
                continue

            flag = _compute_flag(item)
            if flag is None:
                failures += 1
                continue

            planned_updates += 1
            extra["primary_image_is_avatar"] = flag
            if args.apply:
                item.extra = extra
                session.add(item)
                applied_updates += 1
        if args.apply and applied_updates:
            session.commit()
    finally:
        session.close()

    print("Backfill summary")
    print(f"  scanned: {scanned}")
    print(f"  already_set: {already_set}")
    print(f"  would_update: {planned_updates}")
    print(f"  applied_updates: {applied_updates if args.apply else 0}")
    print(f"  failures: {failures}")
    if not args.apply:
        print("Dry-run only; rerun with --apply to persist changes.")


if __name__ == "__main__":
  main()
