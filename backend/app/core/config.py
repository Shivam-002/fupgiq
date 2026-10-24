from datetime import date
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    name: str = "Wind Forecast API"
    version: str = "1.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    cors_origins: list[str] = ["http://localhost:5173"]

    # simulation range
    first_day: date = date(2026, 1, 1)
    last_day: date = date(2026, 1, 31)
    track_record_days: int = Field(default=30, ge=1)

    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    elexon_timeout_seconds: float = Field(default=10.0, gt=0)
    elexon_retries: int = Field(default=2, ge=0)
    request_timeout_seconds: float = Field(default=25.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
