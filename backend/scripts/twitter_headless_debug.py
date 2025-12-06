from __future__ import annotations

import argparse
import logging
import os
import sys

from app.core.logging import configure_logging
from app.services.twitter_headless import resolve_twitter_video_headless

logger = logging.getLogger(__name__)


def _default_timeout() -> float:
    try:
        return float(os.getenv("TWITTER_HEADLESS_TIMEOUT_SECS", "15"))
    except ValueError:
        return 15.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Debug Twitter/X headless video resolution for a single URL."
    )
    parser.add_argument(
        "url",
        help="Twitter/X status URL to resolve (e.g. https://x.com/.../status/...).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=_default_timeout(),
        help="Timeout in seconds for Playwright navigation (default: env TWITTER_HEADLESS_TIMEOUT_SECS or 15).",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Logging level (default: env LOG_LEVEL or INFO).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)
    logger.info(
        "twitter_headless_cli_start url=%s timeout=%.1fs log_level=%s",
        args.url,
        args.timeout,
        args.log_level,
    )

    result = resolve_twitter_video_headless(args.url, timeout=args.timeout)
    if not result:
        logger.info("twitter_headless_cli_result outcome=no_video url=%s", args.url)
        print("No video resolved (see logs for details).")
        return 1

    logger.info(
        "twitter_headless_cli_result outcome=success url=%s video_type=%s",
        args.url,
        result.get("video_type"),
    )
    print("Twitter headless resolution succeeded:")
    print(f"  url:        {args.url}")
    print(f"  video_url:  {result.get('video_url')}")
    print(f"  video_type: {result.get('video_type')}")
    print(f"  poster_url: {result.get('poster_url')}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
