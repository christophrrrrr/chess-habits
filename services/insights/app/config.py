"""Service configuration, read only from environment variables (or a local .env file)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "insights"
    database_url: str = "sqlite:///./insights.db"
    cors_origins: str = "http://localhost:5173"
    db_startup_timeout_seconds: int = 120
    # Base URL of the games service (service-to-service HTTP).
    games_service_url: str = "http://localhost:8001"
    games_service_timeout_seconds: float = 10.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
