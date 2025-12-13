from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Iterable
from contextlib import nullcontext

from app import models, schemas
from app.core.config import get_settings, reset_settings
from app.core.logging import UtcFormatter, configure_logging
from app.core import urls
from app.database import Base, SessionLocal, configure_engine
from app.services import ingestion_service, items_service
from app.services.deepseek_client import DeepSeekTagResult, generate_tags_for_text

logger = logging.getLogger(__name__)


def _default_path() -> Path:
    return Path(__file__).resolve().parents[2] / "SCRIPTS_" / "liked_tweets.json"


def _default_log_path() -> Path:
    return Path(__file__).resolve().parents[2] / "deepseek_results.log"


def _load_tweets(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Tweets file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Expected liked_tweets.json to contain a list of tweets.")
    return data


def _get_user(db: SessionLocal, email: str) -> models.User:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise SystemExit(f"User not found for email: {email}")
    return user


def _canonical_url(tweet: dict) -> str:
    handle = tweet.get("user_handle") or tweet.get("username")
    tweet_id = tweet.get("tweet_id")
    if not handle or not tweet_id:
        raise ValueError("Tweet is missing user_handle or tweet_id.")
    return f"https://x.com/{handle}/status/{tweet_id}"


def _title_from_content(text: str | None, max_len: int = 80) -> str:
    if not text:
        return "Twitter Like"
    stripped = text.strip().replace("\n", " ")
    return stripped if len(stripped) <= max_len else stripped[: max_len - 1].rstrip() + "…"


def _combine_tags(result: DeepSeekTagResult) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for tag in result.tags:
        if not tag:
            continue
        cleaned = tag.strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            tags.append(cleaned)
    if result.category:
        category = result.category.strip()
        key = category.lower()
        if category and key not in seen:
            seen.add(key)
            tags.append(category)
    return tags


def _report_line(url: str, tag_result: DeepSeekTagResult) -> str:
    tag_preview = ", ".join(tag_result.tags or [])
    return f"{url} -> [{tag_preview}] — {tag_result.summary}"


def process_tweets(
    tweets: Iterable[dict],
    *,
    user_email: str,
    limit: int | None = None,
    dry_run: bool = False,
    log_path: Path | None = None,
) -> int:
    settings = get_settings()
    engine = configure_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    processed = created = updated = failures = 0
    sample_output: list[str] = []

    log_cm = log_path.open("a", encoding="utf-8") if log_path else nullcontext(None)
    with SessionLocal() as db, log_cm as log_file:
        user = _get_user(db, user_email)

        for raw in tweets:
            if limit is not None and processed >= limit:
                break
            processed += 1

            try:
                url = _canonical_url(raw)
                normalized = urls.normalize_url(url).url
                content = raw.get("tweet_content") or ""
                title = _title_from_content(content)
                tag_result = generate_tags_for_text(content)
                tags = _combine_tags(tag_result)
            except Exception as exc:  # pylint: disable=broad-except
                failures += 1
                logger.warning("Skipping tweet due to error: %s", exc)
                continue

            line = _report_line(normalized, tag_result)
            if log_file:
                log_file.write(line + "\n")

            if dry_run:
                sample_output.append(line)
                print(line)
                continue

            existing = (
                db.query(models.Item)
                .filter(models.Item.user_id == user.id, models.Item.source_url == normalized)
                .first()
            )

            if existing:
                items_service.set_item_tags(db, user, existing, tags)
                updated += 1
                logger.info("Updated tags for existing item %s", normalized)
            else:
                payload = schemas.UrlIngestionRequest(url=normalized, title=title, tags=tags)
                try:
                    ingestion_service.ingest_url(db, user, payload)
                    created += 1
                    logger.info("Ingested new tweet %s", normalized)
                except Exception as exc:  # pragma: no cover - defensive
                    failures += 1
                    logger.warning("Failed to ingest %s: %s", normalized, exc)
                    continue

    summary_line = (
        "import_liked_tweets_complete processed=%s created=%s updated=%s failures=%s",
        processed,
        created,
        updated,
    )
    logger.info(*summary_line)
    if log_path:
        summary_text = (
            f"Processed {processed} tweets (created={created}, updated={updated}, failures={failures})"
        )
        summary_block = ["", summary_text]
        for line in sample_output[:3]:
            summary_block.append(f"Example: {line}")
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write("\n".join(summary_block) + "\n")

    print(
        f"Processed {processed} tweets (created={created}, updated={updated}, failures={failures})"
    )
    if sample_output:
        print("Examples:")
        for line in sample_output[:3]:
            print(f"  {line}")
    return 0 if failures == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import liked tweets and tag them using DeepSeek."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=str(_default_path()),
        help="Path to liked_tweets.json (default: ../SCRIPTS_/liked_tweets.json)",
    )
    parser.add_argument(
        "--user-email",
        required=True,
        help="Email of the user who should own the imported items.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of tweets to process.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print tagging output without writing to the database.",
    )
    parser.add_argument(
        "--log",
        nargs="?",
        const=str(_default_log_path()),
        help="Write tagging output to a log file (default: deepseek_results.log in APP_). "
        "Provide a custom path to override.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Log level (default: INFO).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)
    log_path = Path(args.log) if args.log else None
    if log_path:
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(
            UtcFormatter("%(asctime)sZ | %(levelname)s | %(name)s | %(message)s")
        )
        file_handler.setLevel(args.log_level.upper())
        logging.getLogger().addHandler(file_handler)
    reset_settings()  # ensure fresh settings if env changed

    tweets = _load_tweets(Path(args.path))
    return process_tweets(
        tweets,
        user_email=args.user_email,
        limit=args.limit,
        dry_run=args.dry_run,
        log_path=log_path,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main())
