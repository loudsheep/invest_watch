from celery import Celery
from investwatch_common.celery_routes import TASK_ROUTES
from investwatch_common.config import settings

celery_app = Celery(
    "investwatch",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.task_routes = TASK_ROUTES
