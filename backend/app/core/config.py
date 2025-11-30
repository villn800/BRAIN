from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Centralized configuration for the BRAIN backend."""

    PROJECT_NAME: str = Field(default="BRAIN Inspiration Vault")
    API_V1_PREFIX: str = Field(default="/api")
    DATABASE_URL: str = Field(default="postgresql://brain:brain@db:5432/brain")
    STORAGE_ROOT: Path = Field(default=Path("/mnt/brain_vault"))
    SECRET_KEY: str = Field(
        default="dev-secret-change-me-please-32-bytes!",
        description="Used for signing auth tokens; override in production.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, ge=5)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("API_V1_PREFIX")
    def ensure_prefix(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return "/api"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        if len(normalized) > 1:
            normalized = normalized.rstrip("/")
        return normalized


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so loads/deserialization happen once."""
    return Settings()
