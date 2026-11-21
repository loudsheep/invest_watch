import re
from datetime import UTC
from pathlib import Path

from investwatch_common.db import SessionLocal
from investwatch_common.logging import get_logger
from investwatch_common.models import Document, Source
from investwatch_common.redis_client import get_redis
from investwatch_common.schemas import RawDocument
from sqlalchemy.exc import IntegrityError

from .celery_app import celery_app
from .collectors import REGISTRY
from .discovery import discovery_config
from .normalize import content_hash, normalize_text
from .storage import put_object

logger = get_logger(__name__)

SCAN_STAGE_CHANNEL = "scan:stages"
CONFIG_PATH = Path("/app/config/sources.yaml")


def _publish_scan_stage(
    scan_id: str, stage: str, status: str, message: str | None = None, data: dict | None = None
):
    import json

    payload = {"scan_id": scan_id, "stage": stage, "status": status, "message": message, "data": data or {}}
    get_redis().publish(SCAN_STAGE_CHANNEL, json.dumps(payload))


RISK_SENTENCE = re.compile(r"ryzyk|strat|traci|nie gwarantuj|mo(ż|z)esz stracić", re.IGNORECASE)


def _removed_risk_statements(previous_text: str, current_text: str) -> list[str]:
    split = re.compile(r"(?<=[.!?])\s+|\n+")
    current = current_text.lower()
    return [
        sentence.strip()
        for sentence in split.split(previous_text)
        if RISK_SENTENCE.search(sentence) and sentence.strip().lower() not in current
    ]


def _detect_change(db, raw: RawDocument, normalized: str) -> None:
    """Flags a re-crawled URL whose risk statements disappeared since the last snapshot."""
    previous = (
        db.query(Document).filter(Document.url == raw.url).order_by(Document.fetched_at.desc()).first()
    )
    if previous is None or not previous.text_normalized:
        return
    removed = _removed_risk_statements(previous.text_normalized, normalized)
    if removed:
        raw.computed_styles = {
            **(raw.computed_styles or {}),
            "change_detection": {
                "previous_document_id": previous.id,
                "previous_fetched_at": previous.fetched_at.isoformat() if previous.fetched_at else None,
                "removed_risk_statements": removed[:5],
            },
        }


def _store_raw_document(db, source_id: int, raw: RawDocument) -> Document | None:
    normalized = normalize_text(raw.content)
    doc_hash = content_hash(normalized)

    existing = db.query(Document).filter(Document.content_hash == doc_hash).first()
    if existing:
        logger.info("duplicate_document_skipped", url=raw.url, hash=doc_hash)
        return None

    _detect_change(db, raw, normalized)

    html_key = None
    screenshot_key = None
    if raw.html:
        html_key = f"html/{doc_hash}.html"
        put_object(html_key, raw.html.encode("utf-8"), "text/html")
    if raw.screenshot_png:
        screenshot_key = f"screenshots/{doc_hash}.png"
        put_object(screenshot_key, raw.screenshot_png, "image/png")

    doc = Document(
        source_id=source_id,
        url=raw.url,
        canonical_url=raw.canonical_url or raw.url,
        platform=raw.platform,
        author=raw.author,
        title=raw.title,
        published_at=raw.published_at,
        content=raw.content,
        content_hash=doc_hash,
        text_normalized=normalized,
        minio_html_key=html_key,
        minio_screenshot_key=screenshot_key,
        computed_styles=raw.computed_styles,
    )
    db.add(doc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.info("duplicate_document_race", url=raw.url)
        return None
    db.refresh(doc)
    return doc


@celery_app.task(name="scraper_worker.tasks.run_collector")
def run_collector(source_name: str):
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.name == source_name, Source.enabled.is_(True)).first()
        if source is None:
            logger.warning("source_not_found_or_disabled", source=source_name)
            return

        collector_cls = REGISTRY.get(source.type)
        if collector_cls is None:
            logger.error("no_collector_registered", type=source.type)
            return

        collector = collector_cls({**discovery_config(db), **(source.config or {})})
        count = 0
        for candidate in collector.discover():
            raw = collector.fetch(candidate)
            if raw is None:
                continue
            doc = _store_raw_document(db, source.id, raw)
            if doc is not None:
                count += 1
                celery_app.send_task("ai_worker.tasks.process_document", args=[doc.id])

        from datetime import datetime

        source.last_crawl_at = datetime.now(UTC)
        db.commit()
        logger.info("collector_run_complete", source=source_name, new_documents=count)
    finally:
        db.close()


@celery_app.task(name="scraper_worker.tasks.scan_url_now")
def scan_url_now(url: str, scan_id: str):
    """Used by the 'Scan URL now' dashboard feature - fetches one URL live and
    streams pipeline stages over Redis pub/sub -> api -> Socket.io."""
    from .collectors.open_web import OpenWebCollector

    db = SessionLocal()
    stage = "fetch"
    try:
        try:
            _publish_scan_stage(scan_id, "fetch", "running")
            source = db.query(Source).filter(Source.name == "open-web").first()
            collector = OpenWebCollector((source.config if source else {}) or {})
            raw = collector.fetch(url)
            if raw is None:
                _publish_scan_stage(
                    scan_id, "fetch", "error", "Nie udało się pobrać strony: sprawdź adres, dostępność lub robots.txt"
                )
                return
            _publish_scan_stage(scan_id, "fetch", "done")

            stage = "preprocess"
            _publish_scan_stage(scan_id, "preprocess", "running")
            doc = _store_raw_document(db, source.id if source else 1, raw)
            if doc is None:
                _publish_scan_stage(scan_id, "preprocess", "done", "Duplikat: ta treść jest już w bazie")
                existing = db.query(Document).filter(Document.content_hash == content_hash(normalize_text(raw.content))).first()
                finding_ids = [f.id for f in existing.findings] if existing else []
                message = (
                    f"Ta treść była już skanowana, istniejące findingi: {len(finding_ids)}"
                    if finding_ids
                    else "Ta treść była już skanowana i nie dała żadnego findingu"
                )
                _publish_scan_stage(scan_id, "done", "done", message, {"finding_ids": finding_ids})
                return
            _publish_scan_stage(scan_id, "preprocess", "done")

            celery_app.send_task("ai_worker.tasks.process_document", args=[doc.id, scan_id])
        except Exception as exc:
            logger.exception("scan_failed", scan_id=scan_id, stage=stage)
            _publish_scan_stage(scan_id, stage, "error", str(exc)[:200])
            raise
    finally:
        db.close()
