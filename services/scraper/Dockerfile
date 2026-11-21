FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY common /app/common
COPY services/scraper /app/services/scraper

WORKDIR /app/services/scraper
RUN uv pip install --system --no-cache -e . -e ../../common
RUN playwright install --with-deps chromium

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "-Q", "scraping"]
