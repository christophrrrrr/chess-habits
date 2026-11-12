from alembic import command
from alembic.config import Config
from conftest import PGN
from sqlalchemy import create_engine, text

from app.db import MIGRATIONS_DIR


def _cfg(url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_0002_backfills_existing_games(tmp_path):
    url = f"sqlite:///{(tmp_path / 'm.db').as_posix()}"
    command.upgrade(_cfg(url), "0001")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO players (id, platform, username, created_at, updated_at) "
                "VALUES (1, 'chesscom', 'chrisaxm', '2026-11-12', '2026-11-12')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO games (player_id, platform_game_id, time_class, time_control, "
                "rated, ended_at, player_color, opponent_username, result, result_detail, "
                "ply_count, pgn) VALUES (1, 'g1', 'blitz', '180+2', 1, '2026-10-01 18:10:00', "
                "'black', 'x', 'loss', 'resigned', 5, :pgn)"
            ),
            {"pgn": PGN},
        )
    command.upgrade(_cfg(url), "head")
    with engine.connect() as conn:
        row = conn.execute(text("SELECT started_at, termination, final_material FROM games")).one()
    assert str(row[0]).startswith("2026-10-01 18:00:05")
    assert row[1] == "chrisaxm won by resignation"
    assert row[2] == -5
    command.downgrade(_cfg(url), "0001")
    engine.dispose()
