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
    """Re-reads data/registry_seed.json for new/changed entities. The real
    KNF/ESMA sync endpoints were not available at build time (see
    docs/OPEN_QUESTIONS.md); this currently re-applies the local snapshot,
    which is safe to run repeatedly (upsert by name)."""
    import json
    from pathlib import Path

    from investwatch_common.models import Entity, EntityAlias

    path = Path("/app/data/registry_seed.json")
    if not path.exists():
        logger.warning("registry_seed_missing")
        return

    db = SessionLocal()
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
        for entity_data in registry.get("entities", []):
            entity = db.query(Entity).filter(Entity.name == entity_data["name"]).first()
            if entity is None:
                entity = Entity(
                    name=entity_data["name"],
                    type=entity_data.get("type"),
                    authorized=entity_data.get("authorized"),
                    source=entity_data.get("source"),
                    domains=entity_data.get("domains", []),
                )
                db.add(entity)
                db.commit()
                db.refresh(entity)
                for alias in entity_data.get("aliases", []):
                    db.add(EntityAlias(entity_id=entity.id, alias=alias))
                db.commit()
        logger.info("registry_sync_complete", count=len(registry.get("entities", [])))
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
