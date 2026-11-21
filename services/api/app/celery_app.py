from celery import Celery
from investwatch_common.config import settings

celery_app = Celery(
    "investwatch",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
