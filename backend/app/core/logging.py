from __future__ import annotations

import logging
import time
from logging.config import dictConfig

_LOG_CONFIGURED = False


class UtcFormatter(logging.Formatter):
    converter = time.gmtime


def configure_logging(level: str = "INFO") -> None:
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    normalised_level = level.upper()
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": "app.core.logging.UtcFormatter",
                "fmt": "%(asctime)sZ | %(levelname)s | %(name)s | %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"level": normalised_level, "handlers": ["console"]},
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": normalised_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": normalised_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    dictConfig(logging_config)
    _LOG_CONFIGURED = True
