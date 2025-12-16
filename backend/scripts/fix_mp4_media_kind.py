"""
Normalize media_kind for items that have mp4 file paths but are marked as images.

This prevents the frontend from trying to render mp4s as <img> sources (which
shows broken thumbnails) and ensures they carry the video badge. Safe by
default; pass --apply to persist.
"""

from __future__ import annotations

import argparse
from typing import Optional

from sqlalchemy import select

from app import models
from app.core.logging import configure_logging
from app.database import SessionLocal, configure_engine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set extra.media_kind to 'video' for items with mp4 file_path."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes (default is dry-run).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N items (default: all).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    args = parser.parse_args()
    args.dry_run = not args.apply
    return args


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)
    configure_engine()

    updated = 0
    scanned = 0

    with SessionLocal() as db:
        query = select(models.Item).where(
            models.Item.file_path.ilike("%.mp4"),
            models.Item.type == models.ItemType.tweet,
        )
        if args.limit:
            query = query.limit(args.limit)

        for item in db.scalars(query):
            scanned += 1
            extra = dict(item.extra or {})
            media_kind: Optional[str] = extra.get("media_kind")
            if media_kind == "video":
                continue
            extra["media_kind"] = "video"
            # Prefer leaving video_url untouched if present.
            item.extra = extra
            updated += 1
            if not args.dry_run:
                db.add(item)

        if not args.dry_run and updated:
            db.commit()

    print("Fix mp4 media_kind summary")
    print(f"  scanned: {scanned}")
    print(f"  updated: {updated if not args.dry_run else 0}")
    if args.dry_run:
        print("Dry-run only; rerun with --apply to persist changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
