"""Service configuration, read only from environment variables (or a local .env file)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "games"
    # SQLAlchemy URL. Locally defaults to SQLite; in compose/Azure it is an
    # mssql+pymssql:// URL injected as a secret environment variable.
    database_url: str = "sqlite:///./games.db"
    # Comma-separated list of origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:5173"
    # How long to keep retrying the database at startup (Azure SQL serverless
    # can take up to a minute to resume from auto-pause).
    db_startup_timeout_seconds: int = 120
    chesscom_base_url: str = "https://api.chess.com/pub"
    chesscom_user_agent: str = "Kiebitz/0.1 (+https://github.com/christophrrrrr/Kiebitz)"
    chesscom_timeout_seconds: float = 15.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
