"""
Application configuration management.

This module handles all application settings using Pydantic Settings,
enabling configuration through environment variables and .env files.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.

    All settings can be configured via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Application Metadata
    PROJECT_NAME: str = "AI Task Manager"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./taskmanager.db"

    # Security Settings
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    # AI/LLM Configuration
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
    OPENAI_API_KEY: Optional[str] = None
    MAX_CONVERSATION_HISTORY: int = 10
    CONTEXT_WINDOW_SIZE: int = 4000
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 1000

    # Rate Limiting (for future use)
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    @property
    def database_url_sync(self) -> str:
        """
        Get synchronous database URL.

        Converts async database URLs to sync format for Alembic migrations.
        """
        if self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        return self.DATABASE_URL


# Global settings instance
settings = Settings()
