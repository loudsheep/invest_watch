FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY common /app/common
COPY data /app/data
RUN uv pip install --system --no-cache /app/common

WORKDIR /app/common
CMD ["alembic", "upgrade", "head"]
