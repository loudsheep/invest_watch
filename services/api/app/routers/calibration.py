from fastapi import APIRouter, Depends
from investwatch_common.db import get_db
from investwatch_common.models import Finding, Label, User
from investwatch_common.redis_client import get_redis
from investwatch_common.schemas import CalibrationMetrics
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/api/calibration", tags=["calibration"])

THRESHOLD_KEY_PREFIX = "threshold:"


def _labeled_scores(db: Session, module: str) -> list[tuple[float, bool]]:
    rows = (
        db.query(Finding.score, Label.label)
        .join(Label, Label.finding_id == Finding.id)
        .filter(Finding.module == module)
        .all()
    )
    return [(score, bool(label)) for score, label in rows if score is not None]


def _metrics_at_threshold(samples: list[tuple[float, bool]], threshold: float) -> dict:
    tp = sum(1 for score, label in samples if score >= threshold and label)
    fp = sum(1 for score, label in samples if score >= threshold and not label)
    fn = sum(1 for score, label in samples if score < threshold and label)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return {"precision": precision, "recall": recall, "false_positives": fp, "false_negatives": fn}


@router.get("/{module}", response_model=CalibrationMetrics)
def get_calibration(module: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    redis_client = get_redis()
    threshold = float(redis_client.get(f"{THRESHOLD_KEY_PREFIX}{module}") or 0.5)

    samples = _labeled_scores(db, module)
    current = _metrics_at_threshold(samples, threshold)

    pr_curve = []
    for i in range(0, 101, 5):
        t = i / 100
        m = _metrics_at_threshold(samples, t)
        pr_curve.append({"threshold": t, "precision": m["precision"], "recall": m["recall"]})

    return CalibrationMetrics(
        module=module,
        threshold=threshold,
        precision=current["precision"],
        recall=current["recall"],
        false_positives=current["false_positives"],
        false_negatives=current["false_negatives"],
        labeled=len(samples),
        positives=sum(1 for _, label in samples if label),
        pr_curve=pr_curve,
    )


@router.put("/{module}/threshold")
def set_threshold(
    module: str,
    threshold: float,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    get_redis().set(f"{THRESHOLD_KEY_PREFIX}{module}", threshold)
    from ..audit import record

    record(db, user.id, "threshold_change", "module", 0, {"module": module, "threshold": threshold})
    return {"module": module, "threshold": threshold}


@router.post("/{module}/retrain")
def retrain(module: str, user: User = Depends(require_admin)):
    """Kick off a retrain job on ai-worker via Celery."""
    from ..celery_app import celery_app

    task = celery_app.send_task("ai_worker.tasks.retrain_classifier", args=[module])
    return {"task_id": task.id, "module": module}
