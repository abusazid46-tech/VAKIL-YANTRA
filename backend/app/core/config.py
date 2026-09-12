import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_default_database_url() -> str:
    # In Vercel serverless environment, SQLite must be written to /tmp
    if os.environ.get("VERCEL"):
        return "sqlite:////tmp/vakil_yantra_dev.db"
    return "sqlite:///./vakil_yantra_dev.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Vakil Yantra API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,https://web-eta-rose-13.vercel.app",
        alias="CORS_ORIGINS",
    )
    jwt_secret: str = "dev-only-change-this-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    frontend_url: str = "http://localhost:3000"
    auth_otp_minutes: int = 10
    auth_token_minutes: int = 60
    auth_email_preview: bool = Field(
        default_factory=lambda: bool(os.environ.get("VERCEL") or not os.environ.get("SMTP_HOST"))
    )
    email_from: str = "Vakil Yantra <no-reply@vakilyantra.app>"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    supabase_project_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "vakil-documents"
    max_upload_bytes: int = 50_000_000
    database_url: str = Field(default_factory=get_default_database_url)
    auto_create_db: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
