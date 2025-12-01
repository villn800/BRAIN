from datetime import datetime, timezone
from pathlib import Path

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from .api import auth, items, tags
from .core.config import get_settings
from .core.logging import configure_logging
from .database import Base, get_db, get_engine
from .schemas import HealthStatus


@asynccontextmanager
async def _lifespan(_: FastAPI):
    Base.metadata.create_all(bind=get_engine())
    yield


def create_app() -> FastAPI:
    """Application factory used by ASGI servers and tests."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    application = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=_lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["content-disposition"],
    )

    application.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    application.include_router(items.router, prefix=settings.API_V1_PREFIX)
    application.include_router(tags.router, prefix=settings.API_V1_PREFIX)
    application.mount(
        "/assets",
        StaticFiles(directory=settings.STORAGE_ROOT, check_dir=False),
        name="assets",
    )

    @application.get("/health", response_model=HealthStatus)
    def health(db: Session = Depends(get_db)) -> HealthStatus:
        db_status = "ok"
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            db_status = "error"

        storage_root: Path = settings.STORAGE_ROOT
        storage_status = "ok" if storage_root.is_dir() else "missing"
        overall = "ok" if db_status == "ok" and storage_status == "ok" else "degraded"
        return HealthStatus(
            status=overall,
            db=db_status,
            storage=storage_status,
            environment=settings.ENVIRONMENT,
            version=settings.APP_VERSION,
            timestamp=datetime.now(timezone.utc),
        )

    return application


app = create_app()
