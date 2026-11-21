"""Initial schema: users, entities, documents, findings, cases, labels, audit_logs

Revision ID: 0001
Revises:
Create Date: 2026-11-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 768


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), server_default="analyst"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "entities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50)),
        sa.Column("authorized", sa.Boolean),
        sa.Column("source", sa.String(100)),
        sa.Column("nip", sa.String(50)),
        sa.Column("krs", sa.String(50)),
        sa.Column("lei", sa.String(20)),
        sa.Column("domains", ARRAY(sa.String)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_entities_authorized", "entities", ["authorized"])
    op.execute("CREATE INDEX idx_entities_name ON entities USING gin (name gin_trgm_ops)")

    op.create_table(
        "entity_aliases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity_id", sa.Integer, sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_entity_aliases_entity_id", "entity_aliases", ["entity_id"])
    op.create_index("idx_entity_aliases_alias", "entity_aliases", ["alias"])

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("type", sa.String(50)),
        sa.Column("enabled", sa.Boolean, server_default=sa.true()),
        sa.Column("config", JSONB),
        sa.Column("last_crawl_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("canonical_url", sa.String(2048)),
        sa.Column("platform", sa.String(100)),
        sa.Column("author", sa.String(500)),
        sa.Column("title", sa.String(500)),
        sa.Column("published_at", sa.DateTime),
        sa.Column("fetched_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("content", sa.Text),
        sa.Column("content_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("text_normalized", sa.Text),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("minio_html_key", sa.String(500)),
        sa.Column("minio_screenshot_key", sa.String(500)),
        sa.Column("computed_styles", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_documents_source_id", "documents", ["source_id"])
    op.create_index("idx_documents_platform", "documents", ["platform"])
    op.execute(
        "CREATE INDEX idx_documents_embedding ON documents "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "mentions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("document_id", sa.Integer, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_id", sa.Integer, sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("role", sa.String(50)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_mentions_document_id", "mentions", ["document_id"])
    op.create_index("idx_mentions_entity_id", "mentions", ["entity_id"])

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("document_id", sa.Integer, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module", sa.String(50)),
        sa.Column("score", sa.Float),
        sa.Column("model_version", sa.Integer, server_default="1"),
        sa.Column("prompt_version", sa.Integer, server_default="1"),
        sa.Column("evidence", sa.Text),
        sa.Column("explanation", sa.Text),
        sa.Column("details", JSONB),
        sa.Column("status", sa.String(50), server_default="new"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_findings_document_id", "findings", ["document_id"])
    op.create_index("idx_findings_module", "findings", ["module"])
    op.create_index("idx_findings_status", "findings", ["status"])
    op.create_index("idx_findings_score", "findings", ["score"])

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("primary_entity_id", sa.Integer, sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("finding_ids", ARRAY(sa.Integer)),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(50), server_default="new"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_cases_primary_entity_id", "cases", ["primary_entity_id"])
    op.create_index("idx_cases_status", "cases", ["status"])

    op.create_table(
        "labels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("finding_id", sa.Integer, sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.Boolean),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_labels_finding_id", "labels", ["finding_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(100)),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.Integer),
        sa.Column("details", JSONB),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("labels")
    op.drop_table("cases")
    op.drop_table("findings")
    op.drop_table("mentions")
    op.drop_table("documents")
    op.drop_table("sources")
    op.drop_table("entity_aliases")
    op.drop_table("entities")
    op.drop_table("users")
