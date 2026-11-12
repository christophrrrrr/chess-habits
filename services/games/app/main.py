"""FastAPI application for the Kiebitz games service."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.db import get_engine, run_migrations, wait_for_database
from app.logging_setup import RequestLogMiddleware, configure_logging
from app.routes import router

log = logging.getLogger(__name__)


def _prepare_database() -> None:
    settings = get_settings()
    wait_for_database(get_engine(), settings.db_startup_timeout_seconds)
    run_migrations(settings.database_url)
    log.info("database ready, migrations applied")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await run_in_threadpool(_prepare_database)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.service_name)
    app = FastAPI(title="Kiebitz games service", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(RequestLogMiddleware)
    app.include_router(router)
    return app


app = create_app()
