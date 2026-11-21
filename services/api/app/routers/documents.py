import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from investwatch_common.db import get_db
from investwatch_common.models import Document, User
from sqlalchemy.orm import Session

from ..audit import record
from ..auth import get_current_user
from ..storage import get_object

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/{document_id}/screenshot")
def get_screenshot(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.get(Document, document_id)
    if doc is None or not doc.minio_screenshot_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Screenshot not found")

    record(db, user.id, "evidence_access", "document", doc.id, {"key": doc.minio_screenshot_key})
    data = get_object(doc.minio_screenshot_key)
    return StreamingResponse(io.BytesIO(data), media_type="image/png")


@router.get("/{document_id}/html")
def get_html(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.get(Document, document_id)
    if doc is None or not doc.minio_html_key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "HTML not found")

    record(db, user.id, "evidence_access", "document", doc.id, {"key": doc.minio_html_key})
    data = get_object(doc.minio_html_key)
    return StreamingResponse(io.BytesIO(data), media_type="text/html")
