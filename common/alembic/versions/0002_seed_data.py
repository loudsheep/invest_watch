"""Seed sources, dev users, entity registry snapshot

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-21
"""
import json
import os

from alembic import op
import sqlalchemy as sa
from argon2 import PasswordHasher

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# Dev-only seed credentials (username/password: analyst/changeme-dev, admin/changeme-dev).
# Rotate immediately for any non-local deployment.
DEV_PASSWORD_HASH = PasswordHasher().hash("changeme-dev")

REGISTRY_SEED_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "registry_seed.json"
)


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            "INSERT INTO sources (name, type, enabled, config) VALUES "
            "(:n, :t, true, :c)"
        ),
        [
            {"n": "open-web", "t": "open_web", "c": json.dumps({"max_depth": 3, "rate_limit_per_sec": 1})},
            {"n": "youtube", "t": "youtube", "c": json.dumps({})},
            {"n": "dataset", "t": "dataset", "c": json.dumps({})},
            {"n": "demo-sites", "t": "demo_sites", "c": json.dumps({"base_url": "http://demo-sites:8080"})},
        ],
    )

    conn.execute(
        sa.text(
            "INSERT INTO users (email, username, password_hash, role) VALUES "
            "(:e, :u, :p, :r)"
        ),
        [
            {"e": "analyst@investwatch.local", "u": "analyst", "p": DEV_PASSWORD_HASH, "r": "analyst"},
            {"e": "admin@investwatch.local", "u": "admin", "p": DEV_PASSWORD_HASH, "r": "admin"},
        ],
    )

    if os.path.exists(REGISTRY_SEED_PATH):
        with open(REGISTRY_SEED_PATH, encoding="utf-8") as f:
            registry = json.load(f)

        for entity in registry.get("entities", []):
            result = conn.execute(
                sa.text(
                    "INSERT INTO entities (name, type, authorized, source, domains) "
                    "VALUES (:name, :type, :authorized, :source, :domains) RETURNING id"
                ),
                {
                    "name": entity["name"],
                    "type": entity.get("type"),
                    "authorized": entity.get("authorized"),
                    "source": entity.get("source"),
                    "domains": entity.get("domains", []),
                },
            )
            entity_id = result.scalar()
            for alias in entity.get("aliases", []):
                conn.execute(
                    sa.text("INSERT INTO entity_aliases (entity_id, alias) VALUES (:eid, :alias)"),
                    {"eid": entity_id, "alias": alias},
                )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM entity_aliases"))
    conn.execute(sa.text("DELETE FROM entities"))
    conn.execute(sa.text("DELETE FROM users"))
    conn.execute(sa.text("DELETE FROM sources"))
