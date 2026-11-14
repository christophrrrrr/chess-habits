"""Database engine, sessions and startup migrations."""

import logging
import time
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

log = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _enable_sqlite_foreign_keys(dbapi_conn, _record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(url: str) -> Engine:
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    elif url.startswith("mssql"):
        kwargs["connect_args"] = {"login_timeout": 60, "timeout": 60}
        kwargs["pool_recycle"] = 1800
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


@lru_cache
def get_engine() -> Engine:
    return make_engine(get_settings().database_url)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


def wait_for_database(engine: Engine, timeout_seconds: int) -> None:
    """Retry until the database accepts connections (handles serverless resume)."""
    deadline = time.monotonic() + timeout_seconds
    delay = 2.0
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if time.monotonic() >= deadline:
                raise
            log.warning("database not reachable yet, retrying in %.0fs", delay)
            time.sleep(delay)
            delay = min(delay * 2, 15.0)


def run_migrations(url: str) -> None:
    """Apply all versioned migrations in migrations/versions (alembic upgrade head)."""
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(cfg, "head")
