from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "VaxInsight"
    APP_ENV: Literal["development", "test", "production"] = "development"
    DEBUG: bool = False

    # PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "vaccine_ai"
    DB_USER: str = "postgres"
    DB_PASSWORD: str
    DB_SSL_MODE: str = "prefer"

    # Authentication and security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ISSUER: str = "vaxinsight-api"
    JWT_AUDIENCE: str = "vaxinsight-mobile"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    INVITATION_EXPIRE_HOURS: int = 24
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 10
    ALLOW_COMMUNITY_REGISTRATION: bool = True

    # Email delivery
    # Leave unset when the native mobile deep link is the only client entry point.
    ACCOUNT_ACTION_BASE_URL: str | None = None
    MOBILE_DEEP_LINK_BASE_URL: str | None = "vaxinsight://"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_USE_TLS: bool = True

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT: int = 10
    REGISTER_RATE_LIMIT: int = 5
    INVITATION_RATE_LIMIT: int = 10
    RESET_RATE_LIMIT: int = 5
    NARRATIVE_RATE_LIMIT: int = 10
    QUESTION_RATE_LIMIT: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_CLEANUP_BATCH_SIZE: int = 500
    RATE_LIMIT_CLEANUP_MAX_BATCHES: int = 10

    # Browser clients are optional; native mobile clients do not need CORS.
    CORS_ALLOWED_ORIGINS: str = ""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_security_settings(self):
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters")
        if self.ALGORITHM != "HS256":
            raise ValueError("Only the configured HS256 JWT algorithm is supported")
        if self.APP_ENV == "production" and self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        if self.APP_ENV == "production" and self.DB_SSL_MODE != "require":
            raise ValueError("DB_SSL_MODE must be require in production")
        if self.APP_ENV == "production" and (not self.SMTP_HOST or not self.SMTP_FROM):
            raise ValueError("SMTP_HOST and SMTP_FROM are required in production")
        if self.APP_ENV == "production" and not self.SMTP_USE_TLS:
            raise ValueError("SMTP_USE_TLS must be true in production")
        if self.APP_ENV == "production":
            if self.ACCOUNT_ACTION_BASE_URL and not self.ACCOUNT_ACTION_BASE_URL.startswith(
                "https://"
            ):
                raise ValueError("ACCOUNT_ACTION_BASE_URL must use HTTPS in production")
            if not self.ACCOUNT_ACTION_BASE_URL and not self.MOBILE_DEEP_LINK_BASE_URL:
                raise ValueError(
                    "At least one account action URL must be configured in production"
                )
        if self.APP_ENV == "production" and not self.RATE_LIMIT_ENABLED:
            raise ValueError("RATE_LIMIT_ENABLED must be true in production")
        return self


settings = Settings()
