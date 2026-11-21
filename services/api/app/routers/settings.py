from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from investwatch_common.app_settings import DEFAULTS, get_all_settings, set_setting
from investwatch_common.db import get_db
from investwatch_common.models import AppSetting, Entity, Source, User
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..audit import record
from ..auth import get_current_user, require_admin
from ..celery_app import celery_app

router = APIRouter(prefix="/api/settings", tags=["settings"])

REGISTRY_LAST_SYNC_KEY = "registry_last_sync"


class SettingUpdate(BaseModel):
    value: Any


class SourceUpdate(BaseModel):
    enabled: bool


@router.get("")
def get_settings(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    registry_counts = dict(
        db.query(Entity.source, func.count(Entity.id)).group_by(Entity.source).all()
    )
    last_sync = db.get(AppSetting, REGISTRY_LAST_SYNC_KEY)
    return {
        "settings": get_all_settings(db),
        "sources": [
            {"name": s.name, "type": s.type, "enabled": s.enabled, "last_crawl_at": s.last_crawl_at}
            for s in db.query(Source).order_by(Source.name).all()
        ],
        "registry": {
            "entities_by_source": registry_counts,
            "authorized": db.query(func.count(Entity.id)).filter(Entity.authorized.is_(True)).scalar(),
            "unauthorized": db.query(func.count(Entity.id)).filter(Entity.authorized.is_(False)).scalar(),
            "last_sync": last_sync.value if last_sync else None,
        },
    }


@router.put("/sources/{name}")
def update_source(
    name: str,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    source = db.query(Source).filter(Source.name == name).first()
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found")
    source.enabled = payload.enabled
    db.commit()
    record(db, user.id, "source_toggle", "source", source.id, {"name": name, "enabled": payload.enabled})
    return {"name": name, "enabled": source.enabled}


@router.post("/sources/{name}/run")
def run_source(name: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if db.query(Source).filter(Source.name == name).first() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found")
    task = celery_app.send_task("scraper_worker.tasks.run_collector", args=[name])
    record(db, user.id, "source_run", "source", 0, {"name": name})
    return {"task_id": task.id}


@router.post("/registry-sync")
def trigger_registry_sync(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    task = celery_app.send_task("scheduler.tasks.registry_sync")
    record(db, user.id, "registry_sync", "registry", 0, {})
    return {"task_id": task.id}


@router.put("/{key}")
def update_setting(
    key: str,
    payload: SettingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if key not in DEFAULTS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown setting")
    if type(payload.value) is not type(DEFAULTS[key]):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid value type")
    set_setting(db, key, payload.value)
    record(db, user.id, "setting_change", "setting", 0, {"key": key, "value": payload.value})
    return {"key": key, "value": payload.value}
