import io
import json
import zipfile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from investwatch_common.db import get_db
from investwatch_common.models import Document, User
from sqlalchemy.orm import Session

from ..audit import record
from ..auth import get_current_user
from ..evidence import build_manifest, load_artifacts
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


def _document(db: Session, document_id: int) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc


@router.get("/{document_id}/evidence")
def get_evidence_manifest(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = _document(db, document_id)
    record(db, user.id, "evidence_access", "document", doc.id, {"kind": "manifest"})
    return build_manifest(doc, load_artifacts(doc))


@router.get("/{document_id}/evidence.zip")
def download_evidence_package(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = _document(db, document_id)
    artifacts = load_artifacts(doc)
    manifest = build_manifest(doc, artifacts)
    record(db, user.id, "evidence_access", "document", doc.id, {"kind": "package"})

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in artifacts.items():
            archive.writestr(name, data)
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="evidence-{doc.id}.zip"'},
    )
