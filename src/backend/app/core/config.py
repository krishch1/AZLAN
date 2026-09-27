from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ----------------------------------------------------
    # Application Configuration
    # ----------------------------------------------------
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # ----------------------------------------------------
    # Database Configuration
    # ----------------------------------------------------
    # Using asyncpg driver for PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://azlan:azlan_dev_only@localhost:5432/azlan"
    )
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_RECYCLE: int = Field(default=1800)
    DB_POOL_TIMEOUT: int = Field(default=30)

    # ----------------------------------------------------
    # Placeholder configurations for future sprint tasks
    # ----------------------------------------------------
    # Auditing and Discovery limits (Phase 2 & 4)
    MAX_AUDIT_DURATION_SECONDS: int = Field(default=3600)
    MAX_CONCURRENCY: int = Field(default=5)
    MAX_REQUESTS_PER_AUDIT: int = Field(default=1000)
    
    # HTTP requests timeouts and budgets
    HTTP_TIMEOUT_SECONDS: float = Field(default=10.0)

    # Pydantic Settings configuration to load from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()
