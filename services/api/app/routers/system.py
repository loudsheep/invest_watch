import time
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends
from investwatch_common.config import settings
from investwatch_common.db import get_db
from investwatch_common.models import Document, Finding, Source, User
from investwatch_common.redis_client import PROXY_CIRCUIT_KEY, PROXY_FAILURES_KEY, get_redis
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..storage import get_client

router = APIRouter(prefix="/api/system", tags=["system"])

SOURCES_CONFIG_PATH = Path("/app/config/sources.yaml")
QUEUES = ("scraping", "ai")


def _http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status < 500
    except Exception:
        return False


ACTIVITY_BUCKET_MINUTES = 5
ACTIVITY_BUCKETS = 12


def _activity(db: Session) -> list[dict]:
    """Documents and findings created per 5-minute bucket over the last hour."""
    step = timedelta(minutes=ACTIVITY_BUCKET_MINUTES)
    now = datetime.now(UTC).replace(tzinfo=None)
    start = (now - step * (ACTIVITY_BUCKETS - 1)).replace(second=0, microsecond=0)
    start -= timedelta(minutes=start.minute % ACTIVITY_BUCKET_MINUTES)
    buckets = [{"t": (start + step * i).isoformat(), "documents": 0, "findings": 0} for i in range(ACTIVITY_BUCKETS)]

    def fill(column, key: str) -> None:
        for (created,) in db.query(column).filter(column >= start).all():
            index = int((created - start) / step)
            if 0 <= index < ACTIVITY_BUCKETS:
                buckets[index][key] += 1

    fill(Document.created_at, "documents")
    fill(Finding.created_at, "findings")
    return buckets


def _recent_findings(db: Session) -> list[dict]:
    rows = db.query(Finding).order_by(Finding.created_at.desc()).limit(6).all()
    return [
        {"id": f.id, "module": f.module, "score": f.score, "title": f.document.title, "created_at": f.created_at}
        for f in rows
    ]


def _check_services(db: Session) -> list[dict]:
    def postgres() -> bool:
        db.execute(text("SELECT 1"))
        return True

    checks = {
        "postgres": postgres,
        "redis": lambda: bool(get_redis().ping()),
        "garage": lambda: get_client().bucket_exists(settings.s3_bucket),
        "searxng": lambda: _http_ok(f"{settings.searxng_url}/healthz") or _http_ok(settings.searxng_url),
        "llm": lambda: _http_ok(f"{settings.llm_base_url.rstrip('/')}/models"),
    }
    results = []
    for name, check in checks.items():
        started = time.monotonic()
        try:
            ok = bool(check())
        except Exception:
            ok = False
        results.append({"name": name, "ok": ok, "latency_ms": round((time.monotonic() - started) * 1000)})
    return results


@router.get("/health")
def system_health(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    redis_client = get_redis()
    schedules = {}
    if SOURCES_CONFIG_PATH.exists():
        config = yaml.safe_load(SOURCES_CONFIG_PATH.read_text(encoding="utf-8"))
        schedules = {s["name"]: s.get("schedule_seconds") for s in config.get("sources", [])}

    doc_counts = dict(db.query(Document.source_id, func.count(Document.id)).group_by(Document.source_id).all())
    collectors = [
        {
            "name": s.name,
            "type": s.type,
            "enabled": s.enabled,
            "last_crawl_at": s.last_crawl_at,
            "schedule_seconds": schedules.get(s.name),
            "documents": doc_counts.get(s.id, 0),
        }
        for s in db.query(Source).order_by(Source.name).all()
    ]

    failures = redis_client.hgetall(PROXY_FAILURES_KEY)
    circuits = redis_client.hgetall(PROXY_CIRCUIT_KEY)
    now = time.time()
    proxy_urls = [u.strip() for u in settings.proxy_urls.split(",") if u.strip()]
    proxies = [
        {
            "url": url,
            "failures": int(failures.get(url, 0)),
            "circuit_open": float(circuits.get(url, 0)) > now,
        }
        for url in proxy_urls
    ]

    return {
        "queues": {name: redis_client.llen(name) for name in QUEUES},
        "collectors": collectors,
        "proxies": proxies,
        "services": _check_services(db),
        "activity": _activity(db),
        "recent_findings": _recent_findings(db),
    }
