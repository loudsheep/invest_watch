-- Runs once when the postgres volume is first created.
-- Table creation and seed data live in Alembic migrations (common/alembic),
-- executed by the one-off `migrate` service.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
