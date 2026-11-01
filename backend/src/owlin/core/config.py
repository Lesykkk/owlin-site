from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    storage_bucket: str = "payment-proofs"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    admin_discord_ids: Annotated[list[str], NoDecode] = []
    discord_bot_token: str | None = None
    discord_guild_id: int | None = None
    discord_spam_trap_channel_id: int | None = None

    @field_validator("cors_origins", "admin_discord_ids", mode="before")
    @classmethod
    def split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("database_url", mode="after")
    @classmethod
    def use_asyncpg_driver(cls, value: str | None) -> str | None:
        # Supabase shows plain postgresql:// strings; SQLAlchemy needs the async driver named.
        if value is None:
            return None
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value.removeprefix(prefix)
        return value

    @field_validator("supabase_url", mode="after")
    @classmethod
    def strip_trailing_slash(cls, value: str | None) -> str | None:
        return value.rstrip("/") if value else None

    @property
    def jwt_issuer(self) -> str:
        return f"{self.supabase_url}/auth/v1"

    @property
    def storage_url(self) -> str:
        return f"{self.supabase_url}/storage/v1"

    @property
    def jwks_url(self) -> str:
        return f"{self.jwt_issuer}/.well-known/jwks.json"

    @property
    def discord_bot_enabled(self) -> bool:
        return bool(self.discord_bot_token and self.discord_guild_id)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
