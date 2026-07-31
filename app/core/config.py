"""Application configuration.

All settings are loaded from environment variables (and a local `.env` file
in development). Access them through the module-level `settings` instance.
"""

import json
from enum import StrEnum
from functools import lru_cache
from typing import Annotated
from urllib.parse import quote_plus

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "Radium API"
    APP_ENV: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # ── Security ─────────────────────────────────────────────
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Database ─────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "radium"
    POSTGRES_PASSWORD: str = "radium"
    POSTGRES_DB: str = "radium"
    DATABASE_URL: str | None = None
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── CORS ─────────────────────────────────────────────────
    # Exact origins, for anything the regex below doesn't cover (e.g. a
    # future custom domain like https://admin.radium.com).
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=list)
    # Matches local dev (any localhost/127.0.0.1/private-LAN origin, any
    # port, http or https) and every Vercel deployment — production domain
    # AND the per-branch/per-PR preview URLs — without needing to hand-add
    # each one. An origin is allowed if it matches CORS_ORIGINS OR this.
    CORS_ORIGIN_REGEX: str | None = (
        r"^(https://[a-z0-9-]+\.vercel\.app"
        r"|https?://(localhost|127\.0\.0\.1"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
        r"|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?)$"
    )

    # ── Rate limiting ────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_STORAGE_URI: str = "memory://"
    # Only enable behind a reverse proxy you control — otherwise clients can
    # spoof X-Forwarded-For to evade rate limits.
    TRUST_PROXY_HEADERS: bool = False

    # ── File uploads ─────────────────────────────────────────
    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    # SVG is deliberately excluded: it can carry <script> and would execute
    # on the API origin when served inline.
    ALLOWED_UPLOAD_EXTENSIONS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["jpg", "jpeg", "png", "webp", "gif", "pdf"]
    )

    # ── Email ────────────────────────────────────────────────
    EMAIL_BACKEND: str = "console"
    EMAIL_FROM: str = "no-reply@radium.local"
    FRONTEND_RESET_PASSWORD_URL: str = "http://localhost:5174/reset-password"

    # ── First superuser ──────────────────────────────────────
    FIRST_SUPERUSER_EMAIL: str = "admin@radium.example"
    FIRST_SUPERUSER_PASSWORD: str = "radium@2026"
    FIRST_SUPERUSER_NAME: str = "Radium Admin"

    @field_validator("CORS_ORIGINS", "ALLOWED_UPLOAD_EXTENSIONS", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Accept either a JSON array or a comma-separated string."""
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def _forbid_insecure_defaults_in_production(self) -> "Settings":
        """Refuse to boot production with any shipped default credential."""
        if self.APP_ENV != Environment.PRODUCTION:
            return self
        insecure = []
        if self.SECRET_KEY == "change-me":
            insecure.append("SECRET_KEY (generate one with: openssl rand -hex 32)")
        if not self.DATABASE_URL and self.POSTGRES_PASSWORD == "radium":
            insecure.append("POSTGRES_PASSWORD")
        if self.FIRST_SUPERUSER_PASSWORD == "radium@2026":
            insecure.append("FIRST_SUPERUSER_PASSWORD")
        if insecure:
            raise ValueError(
                "Refusing to start in production with default values for: "
                + ", ".join(insecure)
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{quote_plus(self.POSTGRES_USER)}:"
            f"{quote_plus(self.POSTGRES_PASSWORD)}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == Environment.PRODUCTION

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
