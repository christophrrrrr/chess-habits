# games service

Tracks chess accounts (the CRUD entity) and imports their games from chess.com, one monthly
archive per request. Owns its own database (`players`, `imported_months`, `games`).

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/players` | Track a chess.com account (checked against chess.com) |
| GET | `/players` | List tracked accounts |
| GET | `/players/{id}` | One account with game counts per time class |
| PATCH | `/players/{id}` | Edit display name / notes |
| DELETE | `/players/{id}` | Stop tracking (deletes its games) |
| GET | `/players/{id}/archives` | Months available on chess.com and which are imported |
| POST | `/players/{id}/imports` | Import one month: `{"month": "2026-10"}` |
| GET | `/players/{id}/games` | Paged games (`time_class`, `since`, `include_pgn`, `limit`, `offset`) |
| GET | `/games/{id}` | One game with PGN |

Interactive docs: `http://localhost:8001/docs` when running via compose.

Past months are immutable on chess.com, so a month that has been fully imported is never
fetched again (cache). If chess.com is down or rate-limits us, the API answers `503` with a
clear message; stored data stays available.

## Run and test locally (without Docker)

```bash
cd services/games
python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt   # Windows
uvicorn app.main:app --reload --port 8001     # uses SQLite (games.db) unless DATABASE_URL is set
pytest --cov                                   # tests + coverage
ruff check . && ruff format --check .
```

## Configuration (environment variables)

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./games.db` | `mssql+pymssql://...` in compose / Azure (secret) |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated UI origins |
| `DB_STARTUP_TIMEOUT_SECONDS` | `120` | Retry window while Azure SQL resumes from auto-pause |

## Migrations

Versioned Alembic migrations in `migrations/versions/` are applied automatically on startup.
New migration: `alembic revision -m "describe change"`, then edit the generated file.
