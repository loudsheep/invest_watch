"""Evidence manifest: SHA-256 of every stored artefact of a document, used for
the evidence package and the case report (chain of custody)."""
import hashlib
import json

from investwatch_common.models import Document

from .storage import get_object


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_artifacts(doc: Document) -> dict[str, bytes]:
    artifacts: dict[str, bytes] = {}
    if doc.minio_html_key:
        artifacts["page.html"] = get_object(doc.minio_html_key)
    if doc.minio_screenshot_key:
        artifacts["screenshot.png"] = get_object(doc.minio_screenshot_key)
    if doc.computed_styles:
        artifacts["computed_styles.json"] = json.dumps(
            doc.computed_styles, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8")
    return artifacts


def build_manifest(doc: Document, artifacts: dict[str, bytes]) -> dict:
    return {
        "document_id": doc.id,
        "url": doc.url,
        "fetched_at": doc.fetched_at.isoformat() if doc.fetched_at else None,
        "content_hash": doc.content_hash,
        "files": {name: {"sha256": _sha256(data), "bytes": len(data)} for name, data in artifacts.items()},
    }
