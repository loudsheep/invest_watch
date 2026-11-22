FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Browser layer first: it is large and rarely changes, so project edits don't re-download Chromium.
RUN uv pip install --system --no-cache playwright \
    && apt-get update && apt-get install -y --no-install-recommends libatomic1 \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY common /app/common
COPY services/scraper /app/services/scraper

WORKDIR /app/services/scraper
RUN uv pip install --system --no-cache -e . -e ../../common

COPY config /app/config
COPY data /app/data

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "-Q", "scraping"]
