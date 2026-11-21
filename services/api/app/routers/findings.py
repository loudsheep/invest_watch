from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from investwatch_common.db import get_db
from investwatch_common.models import Document, Finding, Label, Mention, User
from investwatch_common.schemas import FindingDetail, FindingOut, FindingStatusUpdate, MentionOut
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..audit import record
from ..auth import get_current_user
from ..socket_manager import emit_finding_status_changed

router = APIRouter(prefix="/api/findings", tags=["findings"])

VALID_STATUSES = {"new", "in_review", "confirmed", "dismissed", "escalated"}


@router.get("", response_model=list[FindingOut])
def list_findings(
    module: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    min_score: float | None = None,
    max_score: float | None = None,
    source_platform: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Finding).join(Document)
    if module:
        query = query.filter(Finding.module == module)
    if status_filter:
        query = query.filter(Finding.status == status_filter)
    if min_score is not None:
        query = query.filter(Finding.score >= min_score)
    if max_score is not None:
        query = query.filter(Finding.score < max_score)
    if source_platform:
        query = query.filter(Document.platform == source_platform)
    if date_from:
        query = query.filter(Finding.created_at >= date_from)
    if date_to:
        query = query.filter(Finding.created_at <= date_to)
    return (
        query.order_by(Finding.score.desc()).offset(offset).limit(limit).all()
    )


@router.get("/trend")
def findings_trend(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    rows = (
        db.query(
            func.date_trunc("day", Finding.created_at).label("day"),
            Finding.module,
            func.count(Finding.id).label("count"),
        )
        .group_by("day", Finding.module)
        .order_by("day")
        .all()
    )
    return [{"day": r.day.date().isoformat(), "module": r.module, "count": r.count} for r in rows]


@router.get("/counters")
def findings_counters(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    rows = db.query(Finding.module, func.count(Finding.id)).group_by(Finding.module).all()
    by_module = {module: count for module, count in rows}
    high_risk = db.query(func.count(Finding.id)).filter(Finding.score >= 0.8).scalar()
    return {"by_module": by_module, "high_risk": high_risk}


@router.get("/{finding_id}", response_model=FindingDetail)
def get_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found")
    doc = finding.document
    return FindingDetail(
        id=finding.id,
        document_id=finding.document_id,
        module=finding.module,
        score=finding.score,
        status=finding.status,
        created_at=finding.created_at,
        model_version=finding.model_version,
        prompt_version=finding.prompt_version,
        evidence=finding.evidence,
        explanation=finding.explanation,
        details=finding.details or {},
        document_url=doc.url,
        document_title=doc.title,
        document_platform=doc.platform,
        screenshot_url=f"/api/documents/{doc.id}/screenshot" if doc.minio_screenshot_key else None,
        computed_styles=doc.computed_styles,
        mentions=[
            MentionOut(
                entity_id=m.entity_id, entity_name=m.entity.name, role=m.role, authorized=m.entity.authorized
            )
            for m in db.query(Mention).filter(Mention.document_id == doc.id).all()
        ],
    )


@router.patch("/{finding_id}/status", response_model=FindingOut)
async def update_status(
    finding_id: int,
    payload: FindingStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found")

    finding.status = payload.status
    finding.updated_at = datetime.now(UTC)

    if payload.status in ("confirmed", "dismissed"):
        db.add(Label(finding_id=finding.id, label=(payload.status == "confirmed"), created_by=user.id))

    db.commit()
    db.refresh(finding)

    record(db, user.id, "finding_status_change", "finding", finding.id, {"status": payload.status})
    await emit_finding_status_changed(finding.id, finding.status)
    return finding
