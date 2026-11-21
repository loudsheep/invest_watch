FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY common /app/common
COPY services/ai /app/services/ai

WORKDIR /app/services/ai
RUN uv pip install --system --no-cache -e . -e ../../common

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "-Q", "ai"]
