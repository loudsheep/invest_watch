# 0006. Python backend, Celery task queue, service split

- Status: Accepted
- Date: 2026-11-21

## Context

The specification allows .NET, Python or Node for the backend, requires Python for AI and suggests Socket.io for real-time alerts. Frontend, backend and AI must be separate services.

## Considered options

1. Python everywhere: FastAPI, Celery, Playwright for Python.
2. Node (NestJS, BullMQ) for API and scraper, Python only for AI. Two ecosystems, duplicated schemas, double dependency scanning.
3. .NET. No benefit, another ecosystem.

## Decision

Option 1:

- `api`: FastAPI with REST and `python-socketio`,
- `scraper-worker`: Celery worker with collectors and Playwright,
- `ai-worker`: Celery worker with preprocessing, embeddings, classifiers and LLM,
- `scheduler`: Celery Beat,
- Redis as broker and pub/sub, Postgres with pgvector, MinIO for objects.

Services communicate through queues (`raw_documents`, `findings`). High-risk findings are published over Redis pub/sub and pushed to the dashboard via Socket.io. Shared Pydantic schemas and DB models live in a lightweight `common` package.

## Consequences

- One language and one schema definition for all backend services.
- Workers scale independently by adding container replicas.
