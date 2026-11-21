"""Runs in the scheduler container's own beat process; the actual collector
and cleanup work is dispatched to scraper-worker / run here directly since it
is lightweight DB-only work.
"""
from datetime import UTC, datetime, timedelta

from investwatch_common.config import settings
from investwatch_common.db import SessionLocal
from investwatch_common.logging import get_logger
from investwatch_common.models import Document, Finding

from .celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="scheduler.tasks.registry_sync")
def registry_sync():
    """Pulls the public KNF lists (investment firms, banks, foreign branches, notified
    foreign firms, public warnings); an unreachable list falls back to data/registry_knf.json."""
    from .registry.sync import run

    db = SessionLocal()
    try:
        return run(db)
    finally:
        db.close()


@celery_app.task(name="scheduler.tasks.retention_cleanup")
def retention_cleanup():
    """RODO data minimization (ADR-0019): delete documents with no finding
    older than RETENTION_DAYS_NO_FINDING. Evidence for confirmed findings is
    kept regardless."""
    db = SessionLocal()
    try:
        cutoff = datetime.now(UTC) - timedelta(days=settings.retention_days_no_finding)
        candidates = (
            db.query(Document)
            .outerjoin(Finding, Finding.document_id == Document.id)
            .filter(Finding.id.is_(None), Document.fetched_at < cutoff)
            .all()
        )
        count = len(candidates)
        for doc in candidates:
            db.delete(doc)
        db.commit()
        logger.info("retention_cleanup_complete", deleted=count)
    finally:
        db.close()


@celery_app.task(name="scheduler.tasks.dispatch_collector")
def dispatch_collector(source_name: str):
    celery_app.send_task("scraper_worker.tasks.run_collector", args=[source_name])
