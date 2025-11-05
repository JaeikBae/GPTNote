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
    openai_embedding_model: str = "text-embedding-3-small"
    cors_allow_origins: list[str] = ["*"]
    rag_enabled: bool = True
    rag_default_top_k: int = 3
    rag_local_vector_size: int = 512

    model_config = SettingsConfigDict(env_prefix="MINDDOCK_", env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""

    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings

