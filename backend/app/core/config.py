from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Centralized configuration for the BRAIN backend."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    PROJECT_NAME: str = Field(default="BRAIN Inspiration Vault")
    API_V1_PREFIX: str = Field(default="/api")
    DATABASE_URL: str = Field(default="postgresql://brain:brain@db:5432/brain")
    STORAGE_ROOT: Path = Field(default=Path("/mnt/brain_vault"))
    SECRET_KEY: str = Field(
        default="dev-secret-change-me-please-32-bytes!",
        description="Used for signing auth tokens; override in production.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, ge=5)

    @field_validator("API_V1_PREFIX")
    @classmethod
    def ensure_prefix(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return "/api"
        if not normalized.startswith("/"):
            normalized = f"/{normalized}"
        if len(normalized) > 1:
            normalized = normalized.rstrip("/")
        return normalized

    @field_validator("STORAGE_ROOT", mode="before")
    @classmethod
    def ensure_storage_root(cls, value: str | Path) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise ValueError("STORAGE_ROOT must be an absolute path")
        return path


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so loads/deserialization happen once."""
    return Settings()


def reset_settings() -> None:
    """Clear the cached settings so tests or CLIs can reload from env."""
    get_settings.cache_clear()
