FROM pgvector/pgvector:pg16
COPY infra/init.sql /docker-entrypoint-initdb.d/01-init.sql
