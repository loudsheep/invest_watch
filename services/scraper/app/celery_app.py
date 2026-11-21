from celery import Celery
from investwatch_common.config import settings
from investwatch_common.logging import configure_logging

configure_logging("scraper-worker")

celery_app = Celery(
    "investwatch",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)
celery_app.conf.task_routes = {"scraper_worker.tasks.*": {"queue": "scraping"}}

from celery.signals import worker_ready  # noqa: E402


@worker_ready.connect
def _run_dataset_collector_once(**kwargs):
    """The dataset source has no schedule (runs once); kick it off as soon as
    this worker can accept tasks instead of waiting on scheduler."""
    celery_app.send_task("scraper_worker.tasks.run_collector", args=["dataset"])

