"""Application configuration module."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings for environment configuration."""

    project_name: str = "MindDock API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 60 * 24
    sql_database_url: str = (
        f"sqlite:///{Path(__file__).resolve().parent / 'minddock.db'}"
    )
    storage_dir: Path = Path(__file__).resolve().parent / "storage"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    cors_allow_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_prefix="MINDDOCK_", env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""

    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings

