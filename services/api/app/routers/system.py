import time
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends
from investwatch_common.config import settings
from investwatch_common.db import get_db
from investwatch_common.models import Document, Source, User
from investwatch_common.redis_client import PROXY_CIRCUIT_KEY, PROXY_FAILURES_KEY, get_redis
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user

router = APIRouter(prefix="/api/system", tags=["system"])

SOURCES_CONFIG_PATH = Path("/app/config/sources.yaml")
QUEUES = ("scraping", "ai")


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
    }
