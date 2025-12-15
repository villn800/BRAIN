"""
Bulk refresh existing Twitter/X items to pick up extractor improvements.

Safe by default: runs in dry-run mode unless --apply is provided.
"""

from __future__ import annotations

import argparse
import logging
import time
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import or_, select

from app import models
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database import Base, SessionLocal, configure_engine
from app.services import ingestion_service

logger = logging.getLogger(__name__)


def _bool_arg(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh existing Twitter/X items to backfill media and metadata.",
    )
    parser.add_argument(
        "--user-email",
        required=True,
        help="Email of the user who owns the items.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum number of eligible items to process (default: 200).",
    )
    parser.add_argument(
        "--only-missing-media",
        type=_bool_arg,
        default=True,
        help="If true, restrict to items missing media or marked as avatar-as-media (default: true).",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Re-download media even if already present.",
    )
    parser.add_argument(
        "--update-text",
        action="store_true",
        help="Overwrite title/description/text_content with refreshed values.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.2,
        help="Seconds to sleep between items (default: 0.2).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without writing changes (default).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes. Without this flag the script is a dry-run.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    args = parser.parse_args()
    if not args.apply:
        args.dry_run = True
    return args


def _get_user(db: SessionLocal, email: str) -> models.User:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise SystemExit(f"User not found for email: {email}")
    return user


def _is_twitter_item(item: models.Item) -> bool:
    domain = (item.origin_domain or "").lower()
    if "twitter.com" in domain or "x.com" in domain:
        return True
    if item.source_url:
        parsed = urlparse(item.source_url)
        netloc = parsed.netloc.lower()
        return "twitter.com" in netloc or "x.com" in netloc
    return False


def _is_missing_media(item: models.Item) -> bool:
    if not item.file_path:
        return True
    extra = item.extra or {}
    return bool(extra.get("primary_image_is_avatar"))


def _should_download(item: models.Item, force_download: bool) -> bool:
    return bool(
        force_download
        or not item.file_path
        or (item.extra or {}).get("primary_image_is_avatar")
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)
    settings = get_settings()
    engine = configure_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    counters = {
        "scanned": 0,
        "eligible": 0,
        "refreshed_ok": 0,
        "refreshed_pending": 0,
        "failed": 0,
        "images_downloaded": 0,
        "skipped_no_change": 0,
    }

    with SessionLocal() as db:
        user = _get_user(db, args.user_email)
        query = (
            select(models.Item)
            .where(
                models.Item.user_id == user.id,
                or_(
                    models.Item.type == models.ItemType.tweet,
                    models.Item.origin_domain.ilike("%twitter.com%"),
                    models.Item.origin_domain.ilike("%x.com%"),
                ),
            )
            .order_by(models.Item.created_at.desc())
        )

        for item in db.scalars(query):
            counters["scanned"] += 1
            if args.limit and counters["eligible"] >= args.limit:
                break
            if not _is_twitter_item(item):
                continue
            if args.only_missing_media and not _is_missing_media(item):
                continue

            counters["eligible"] += 1
            download_needed = _should_download(item, args.force_download)

            if args.dry_run:
                print(
                    f"[DRY-RUN] would refresh item_id={item.id} url={item.source_url} "
                    f"download_image={download_needed} update_text={args.update_text}"
                )
                continue

            before_path = item.file_path
            before_extra = dict(item.extra or {})
            before_title = item.title
            before_description = item.description
            before_text = item.text_content
            before_status = item.status

            try:
                refreshed = ingestion_service.refresh_url_item(
                    db,
                    user,
                    item,
                    force_download=args.force_download,
                    update_text=args.update_text,
                )
            except Exception as exc:  # pylint: disable=broad-except
                counters["failed"] += 1
                db.rollback()
                logger.warning("Refresh failed for %s: %s", item.source_url, exc)
                continue

            changed = (
                refreshed.file_path != before_path
                or (refreshed.extra or {}) != before_extra
                or refreshed.status != before_status
                or (
                    args.update_text
                    and (
                        refreshed.title != before_title
                        or refreshed.description != before_description
                        or refreshed.text_content != before_text
                    )
                )
            )

            if refreshed.status == models.ItemStatus.ok:
                counters["refreshed_ok"] += 1
            elif refreshed.status == models.ItemStatus.pending:
                counters["refreshed_pending"] += 1
            else:
                counters["failed"] += 1

            if refreshed.file_path and refreshed.file_path != before_path:
                counters["images_downloaded"] += 1
            if not changed:
                counters["skipped_no_change"] += 1

            if args.sleep:
                time.sleep(args.sleep)

    print("Refresh summary")
    print(f"  scanned: {counters['scanned']}")
    print(f"  eligible: {counters['eligible']}")
    print(f"  refreshed_ok: {counters['refreshed_ok']}")
    print(f"  refreshed_pending: {counters['refreshed_pending']}")
    print(f"  failed: {counters['failed']}")
    print(f"  images_downloaded: {counters['images_downloaded']}")
    print(f"  skipped_no_change: {counters['skipped_no_change']}")
    if args.dry_run:
        print("Dry-run only; rerun with --apply to persist changes.")
    return 0 if counters["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
