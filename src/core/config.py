from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, HttpUrl, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    # Application Metadata
    PROJECT_NAME: str = "FastAPI Multi-Store Engine"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    # DEBUG: bool = False

    # Storage Connection URIs
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/app_db",
        description="Async PostgreSQL connection URI (asyncpg driver)",
    )
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URI",
    )

    # Vector Storage (Qdrant)
    QDRANT_URL: HttpUrl = Field(
        default="http://localhost:6333",
        description="Qdrant vector engine endpoint",
    )
    QDRANT_API_KEY: str | None = Field(
        default=None,
        description="Qdrant API token",
    )

    # Vector Collection Configuration
    COLLECTION_NAME: str = Field(default="sec_qualitative", min_length=1, max_length=64)
    VECTOR_DIMENSION: int = Field(default=768, gt=0)

    LOGFIRE_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()


settings = get_settings()