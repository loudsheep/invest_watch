from celery import Celery
from investwatch_common.config import settings
from investwatch_common.logging import configure_logging

configure_logging("ai-worker")

celery_app = Celery(
    "investwatch",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)
celery_app.conf.task_routes = {"ai_worker.tasks.*": {"queue": "ai"}}
