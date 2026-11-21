FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY common /app/common
COPY services/api /app/services/api

WORKDIR /app/services/api
RUN uv pip install --system --no-cache -e . -e ../../common

EXPOSE 8000
CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
