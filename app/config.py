from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "World of Warcraft Ledger"
    environment: str = "development"
    blizzard_client_id: str
    blizzard_client_secret: SecretStr
    blizzard_region: str = "us"

    @property
    def blizzard_api_base_url(self) -> str:
        return f"https://{self.blizzard_region}.api.blizzard.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
