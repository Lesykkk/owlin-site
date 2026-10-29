from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    # Lists come from the environment as comma-separated strings.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    admin_discord_ids: Annotated[list[str], NoDecode] = []

    @field_validator("cors_origins", "admin_discord_ids", mode="before")
    @classmethod
    def split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
