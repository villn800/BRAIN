"""
Backfill script to align items.created_at with source timestamps.

Useful after bulk imports where items were inserted newest-first, causing
old tweets to appear at the top of the dashboard. Safe by default (dry-run);
pass --apply to persist changes.
"""

from __future__ import annotations

import argparse
import logging
from datetime import timezone

from sqlalchemy import select

from app import models
from app.database import SessionLocal, configure_engine
from app.services.time_utils import parse_metadata_timestamp, parse_twitter_timestamp_from_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set items.created_at from extra.timestamp when available"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N items (default: all)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes (otherwise runs as a dry-run)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    args = parser.parse_args()
    args.dry_run = not args.apply
    return args


def _normalize(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    configure_engine()
    session = SessionLocal()

    scanned = 0
    missing_timestamp = 0
    unparsable = 0
    unchanged = 0
    updated = 0

    try:
        query = select(models.Item).order_by(models.Item.created_at.asc())
        if args.limit:
            query = query.limit(args.limit)

        items = session.scalars(query).all()
        for item in items:
            scanned += 1
            extra = item.extra or {}
            raw_ts = extra.get("timestamp")
            parsed_ts = parse_metadata_timestamp(raw_ts) if raw_ts else None
            if not parsed_ts:
                parsed_ts = parse_twitter_timestamp_from_url(item.source_url)
                if not parsed_ts:
                    if raw_ts:
                        unparsable += 1
                    else:
                        missing_timestamp += 1
                    continue

            existing = _normalize(item.created_at)
            target = parsed_ts.astimezone(timezone.utc)
            if existing and existing == target:
                unchanged += 1
                continue

            updated += 1
            if not args.dry_run:
                item.created_at = target
                session.add(item)
        if not args.dry_run and updated:
            session.commit()
    finally:
        session.close()

    print("Reorder summary")
    print(f"  scanned: {scanned}")
    print(f"  missing_timestamp: {missing_timestamp}")
    print(f"  unparsable_timestamp: {unparsable}")
    print(f"  unchanged: {unchanged}")
    print(f"  updated_created_at: {updated if not args.dry_run else 0}")
    if args.dry_run:
        print("Dry-run only; rerun with --apply to persist changes.")


if __name__ == "__main__":
    main()
