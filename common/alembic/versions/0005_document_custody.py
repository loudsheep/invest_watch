"""Add device screenshot keys and chain-of-custody manifest to documents

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("device_screenshots", postgresql.JSONB, nullable=True))
    op.add_column("documents", sa.Column("custody", postgresql.JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "custody")
    op.drop_column("documents", "device_screenshots")
