"""Deep analysis results per game, computed in the player's browser (positions and Stockfish).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "game_analyses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("player_id", sa.Integer, nullable=False),
        # Id of the game in the games service (other service, so no foreign key).
        sa.Column("game_id", sa.Integer, nullable=False),
        # Which engine and budget produced `moves` (null: positions only, no engine yet).
        sa.Column("engine", sa.String(32), nullable=True),
        sa.Column("final_cp", sa.Integer, nullable=True),
        sa.Column("position_keys", sa.UnicodeText, nullable=False),
        sa.Column("moves", sa.UnicodeText, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("player_id", "game_id", name="uq_game_analyses_player_game"),
    )
    op.create_index("ix_game_analyses_player_id", "game_analyses", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_game_analyses_player_id", table_name="game_analyses")
    op.drop_table("game_analyses")
