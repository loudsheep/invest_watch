from fastapi import APIRouter, Depends
from investwatch_common.db import get_db
from investwatch_common.redis_client import get_redis
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    checks = {"api": "ok"}
    try:
        db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:  # pragma: no cover
        checks["postgres"] = f"error: {exc}"
    try:
        get_redis().ping()
        checks["redis"] = "ok"
    except Exception as exc:  # pragma: no cover
        checks["redis"] = f"error: {exc}"
    return checks
