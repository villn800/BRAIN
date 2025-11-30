from pathlib import Path

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from .api import auth, items
from .core.config import get_settings
from .database import Base, get_db, get_engine
from .schemas import HealthStatus


def create_app() -> FastAPI:
    """Application factory used by ASGI servers and tests."""
    settings = get_settings()
    application = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )

    application.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    application.include_router(items.router, prefix=settings.API_V1_PREFIX)

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
        return HealthStatus(status=overall, db=db_status, storage=storage_status)

    @application.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=get_engine())

    return application


app = create_app()
