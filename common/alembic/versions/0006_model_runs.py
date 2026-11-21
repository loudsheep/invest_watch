"""Add model_runs: history of classifier training runs

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("labels", sa.Integer, nullable=False),
        sa.Column("positives", sa.Integer, nullable=False),
        sa.Column("metrics", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_model_runs_module", "model_runs", ["module"])


def downgrade() -> None:
    op.drop_index("ix_model_runs_module", table_name="model_runs")
    op.drop_table("model_runs")
