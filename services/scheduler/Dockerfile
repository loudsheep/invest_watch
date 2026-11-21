FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY common /app/common
COPY services/scheduler /app/services/scheduler

WORKDIR /app/services/scheduler
RUN uv pip install --system --no-cache -e . -e ../../common

CMD ["celery", "-A", "app.celery_app", "worker", "--beat", "--loglevel=info"]
