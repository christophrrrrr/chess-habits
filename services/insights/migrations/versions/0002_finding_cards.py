"""Findings become cards: contrasts with MDE and a multiple-testing label, or profiles.

Old findings are deleted: runs are recomputed from the games service at any time.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM findings")
    op.execute("DELETE FROM analysis_runs")
    with op.batch_alter_table("findings") as batch:
        batch.drop_column("confidence")
        batch.add_column(sa.Column("kind", sa.String(16), nullable=False))
        batch.add_column(sa.Column("metric", sa.String(16), nullable=False))
        batch.add_column(sa.Column("label", sa.String(24), nullable=False))
        batch.add_column(sa.Column("mde", sa.Float, nullable=True))
        batch.add_column(sa.Column("p_value", sa.Float, nullable=True))
        batch.alter_column("effect", existing_type=sa.Float, nullable=True)
        batch.alter_column("ci_low", existing_type=sa.Float, nullable=True)
        batch.alter_column("ci_high", existing_type=sa.Float, nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM findings")
    op.execute("DELETE FROM analysis_runs")
    with op.batch_alter_table("findings") as batch:
        batch.drop_column("p_value")
        batch.drop_column("mde")
        batch.drop_column("label")
        batch.drop_column("metric")
        batch.drop_column("kind")
        batch.add_column(sa.Column("confidence", sa.String(16), nullable=False))
        batch.alter_column("effect", existing_type=sa.Float, nullable=False)
        batch.alter_column("ci_low", existing_type=sa.Float, nullable=False)
        batch.alter_column("ci_high", existing_type=sa.Float, nullable=False)
