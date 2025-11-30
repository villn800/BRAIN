from __future__ import annotations

from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .core.config import get_settings

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
    future=True,
)

Base = declarative_base()

_engine: Optional[Engine] = None
_engine_url: Optional[str] = None


def configure_engine(database_url: Optional[str] = None) -> Engine:
    """Configure (or reconfigure) the global SQLAlchemy engine."""
    global _engine, _engine_url

    target_url = str(database_url or get_settings().DATABASE_URL)
    if _engine is None or target_url != _engine_url:
        if _engine is not None:
            _engine.dispose()
        _engine = create_engine(target_url, future=True, pool_pre_ping=True)
        SessionLocal.configure(bind=_engine)
        _engine_url = target_url
    return _engine


def get_engine() -> Engine:
    """Return the active SQLAlchemy engine, configuring it if necessary."""
    return configure_engine()


# Ensure the default engine is ready for the application lifecycle.
configure_engine()


def get_db() -> Generator[Session, None, None]:
    """Yield a scoped session per request and ensure it's cleaned up."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
