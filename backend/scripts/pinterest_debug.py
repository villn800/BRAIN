from __future__ import annotations

import argparse
import logging
from urllib.parse import urlparse

from app.services import metadata_service, url_extractors


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Debug Pinterest metadata extraction without persisting."
    )
    parser.add_argument("url", help="Pinterest URL to inspect")
    parser.add_argument(
        "--timeout",
        type=float,
        default=metadata_service.DEFAULT_TIMEOUT,
        help="HTTP timeout in seconds (default: metadata_service.DEFAULT_TIMEOUT)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Log level (DEBUG, INFO, WARN, ERROR). Default: INFO",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    fetch = metadata_service.fetch_html(args.url, timeout=args.timeout)
    domain = urlparse(args.url).netloc

    print(f"status={fetch.status_code} error={fetch.error} length={len(fetch.html or '')}")
    metadata = url_extractors.extract_for_domain(domain, args.url, fetch.html)
    classification = "none"
    if metadata:
        classification = metadata.item_type.value
    else:
        metadata = metadata_service.parse_generic_metadata(args.url, fetch.html)
        classification = metadata.item_type.value

    gate_flag = metadata.extra.get("pinterest_gate") if metadata else None
    print(
        f"classification={classification} "
        f"title={metadata.title if metadata else None} "
        f"image_url={metadata.image_url if metadata else None} "
        f"pinterest_gate={gate_flag}"
    )


if __name__ == "__main__":  # pragma: no cover - debug entrypoint
    main()
