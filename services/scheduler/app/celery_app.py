from pathlib import Path

import yaml
from celery import Celery
from celery.schedules import schedule
from celery.signals import worker_ready
from investwatch_common.celery_routes import TASK_ROUTES
from investwatch_common.config import settings
from investwatch_common.logging import configure_logging

configure_logging("scheduler")

celery_app = Celery(
    "investwatch",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

SOURCES_CONFIG_PATH = Path("/app/config/sources.yaml")


def _build_beat_schedule() -> dict:
    beat_schedule = {
        "registry-sync": {
            "task": "scheduler.tasks.registry_sync",
            "schedule": schedule(run_every=6 * 3600),
        },
        "retention-cleanup": {
            "task": "scheduler.tasks.retention_cleanup",
            "schedule": schedule(run_every=24 * 3600),
        },
    }

    if SOURCES_CONFIG_PATH.exists():
        config = yaml.safe_load(SOURCES_CONFIG_PATH.read_text(encoding="utf-8"))
        for source in config.get("sources", []):
            interval = source.get("schedule_seconds")
            if interval is None:
                continue
            beat_schedule[f"collect-{source['name']}"] = {
                "task": "scheduler.tasks.dispatch_collector",
                "schedule": schedule(run_every=interval),
                "args": [source["name"]],
            }

    return beat_schedule


celery_app.conf.task_routes = TASK_ROUTES
celery_app.conf.beat_schedule = _build_beat_schedule()
celery_app.conf.timezone = "Europe/Warsaw"


@worker_ready.connect
def _sync_registry_on_start(**_kwargs):
    celery_app.send_task("scheduler.tasks.registry_sync")
