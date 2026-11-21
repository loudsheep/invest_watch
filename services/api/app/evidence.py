"""Evidence manifest: SHA-256 of every stored artefact of a document, compared with the
hashes sealed at capture time (chain of custody), used for the evidence package and the
case report."""
from investwatch_common.custody import canonical_json, sha256_hex, verify_custody
from investwatch_common.models import Document

from .storage import get_object


def load_artifacts(doc: Document) -> dict[str, bytes]:
    artifacts: dict[str, bytes] = {}
    if doc.minio_html_key:
        artifacts["page.html"] = get_object(doc.minio_html_key)
    if doc.minio_screenshot_key:
        artifacts["screenshot.png"] = get_object(doc.minio_screenshot_key)
    for name, key in (doc.device_screenshots or {}).items():
        artifacts[f"screenshot-{name}.png"] = get_object(key)
    if doc.computed_styles:
        artifacts["computed_styles.json"] = canonical_json(doc.computed_styles)
    return artifacts


def build_manifest(doc: Document, artifacts: dict[str, bytes]) -> dict:
    manifest = {
        "document_id": doc.id,
        "url": doc.url,
        "fetched_at": doc.fetched_at.isoformat() if doc.fetched_at else None,
        "content_hash": doc.content_hash,
        "files": {name: {"sha256": sha256_hex(data), "bytes": len(data)} for name, data in artifacts.items()},
        "custody": None,
    }
    if doc.custody:
        verification = verify_custody(doc.custody, artifacts)
        manifest["custody"] = {
            "captured_at": doc.custody["captured_at"],
            "manifest_sha256": doc.custody["manifest_sha256"],
            **verification,
        }
    return manifest
