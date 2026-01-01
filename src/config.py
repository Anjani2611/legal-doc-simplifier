"""Configuration management with environment variables"""

import os
import logging
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field, ConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App config
    app_name: str = Field(default="Legal Document Simplifier", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")

    # Database
    database_url: str = Field(default="sqlite:///./test.db", env="DATABASE_URL")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")

    # Redis (optional)
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # API
    api_title: str = Field(default="API", env="API_TITLE")
    api_description: str = Field(default="", env="API_DESCRIPTION")
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    api_v2_prefix: str = Field(default="/api/v2", env="API_V2_PREFIX")

    # Uploads
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=52428800, env="MAX_FILE_SIZE")  # 50MB
    allowed_extensions: List[str] = Field(default=["pdf", "docx", "txt"], env="ALLOWED_EXTENSIONS")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")

    # JWT/Security
    token_expire_minutes: int = Field(default=30, env="TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field(default="HS256", env="ALGORITHM")

    # Sentry (error tracking)
    sentry_dsn: str = Field(default="", env="SENTRY_DSN")

    # Email
    smtp_server: str = Field(default="", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: str = Field(default="", env="SMTP_USER")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")

    # Pydantic v2 Configuration
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables not defined in Settings
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_extensions(cls, v):
        """Parse allowed extensions from comma-separated string"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",") if ext.strip()]
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def parse_bool(cls, v):
        """Parse string boolean values"""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    @field_validator("rate_limit_enabled", mode="before")
    @classmethod
    def parse_rate_limit_bool(cls, v):
        """Parse string boolean for rate limiting"""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    def validate_database_url(self) -> None:
        """Validate database URL is properly configured"""
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

    def validate_production_config(self) -> None:
        """Validate production-specific settings"""
        if self.environment == "production":
            if self.debug:
                raise ValueError("DEBUG must be False in production")
            if self.secret_key == "change-me-in-production":
                raise ValueError("SECRET_KEY must be changed in production")
            if not self.sentry_dsn:
                logger.warning("SENTRY_DSN not set in production; error tracking disabled")


# Load settings with error handling
try:
    settings = Settings()
    settings.validate_database_url()
    settings.validate_production_config()
    logger.info(f"✓ Configuration loaded for {settings.environment}")
    logger.info(f"✓ Debug mode: {settings.debug}")
    logger.info(f"✓ Database: {settings.database_url.split('@')[0] if '@' in settings.database_url else 'SQLite'}")
except Exception as e:
    logger.error(f"✗ Configuration error: {e}")
    raise
