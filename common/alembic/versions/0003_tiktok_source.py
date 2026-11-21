"""Add the tiktok source

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text(
            "INSERT INTO sources (name, type, enabled, config) "
            "SELECT 'tiktok', 'tiktok', true, '{}'::jsonb WHERE NOT EXISTS (SELECT 1 FROM sources WHERE name = 'tiktok')"
        )
    )


def downgrade() -> None:
    op.get_bind().execute(sa.text("DELETE FROM sources WHERE name = 'tiktok'"))
