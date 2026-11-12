"""Initial schema: analysis_runs, findings.

Revision ID: 0001
Revises:
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("player_id", sa.Integer, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("games_analyzed", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("finished_at", sa.DateTime, nullable=True),
        sa.Column("error", sa.Unicode(500), nullable=True),
    )
    op.create_index("ix_analysis_runs_player_id", "analysis_runs", ["player_id"])
    op.create_table(
        "findings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "run_id",
            sa.Integer,
            sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("analysis_key", sa.String(64), nullable=False),
        sa.Column("time_class", sa.String(16), nullable=False),
        sa.Column("title", sa.Unicode(200), nullable=False),
        sa.Column("summary", sa.Unicode(1000), nullable=False),
        sa.Column("effect", sa.Float, nullable=False),
        sa.Column("ci_low", sa.Float, nullable=False),
        sa.Column("ci_high", sa.Float, nullable=False),
        sa.Column("sample_size", sa.Integer, nullable=False),
        sa.Column("confidence", sa.String(16), nullable=False),
        sa.Column("details", sa.UnicodeText, nullable=False),
    )
    op.create_index("ix_findings_run_id", "findings", ["run_id"])


def downgrade() -> None:
    op.drop_table("findings")
    op.drop_table("analysis_runs")
