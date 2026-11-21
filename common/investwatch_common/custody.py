"""Chain of custody for preserved evidence: SHA-256 of every artefact taken at capture
time, sealed with a manifest hash, so later reads can prove nothing was altered."""
import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def _seal(body: dict) -> str:
    return sha256_hex(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def build_custody(url: str, content_hash: str, files: dict[str, bytes], captured_at: datetime | None = None) -> dict:
    body = {
        "url": url,
        "content_hash": content_hash,
        "captured_at": (captured_at or datetime.now(UTC)).isoformat(),
        "files": {name: {"sha256": sha256_hex(data), "bytes": len(data)} for name, data in sorted(files.items())},
    }
    return {**body, "manifest_sha256": _seal(body)}


def verify_custody(custody: dict, files: dict[str, bytes]) -> dict:
    """Per-file result plus whether the manifest itself is intact."""
    body = {key: custody[key] for key in ("url", "content_hash", "captured_at", "files")}
    results = {}
    for name, meta in custody["files"].items():
        data = files.get(name)
        results[name] = {
            "sha256": meta["sha256"],
            "bytes": meta["bytes"],
            "status": "missing" if data is None else ("ok" if sha256_hex(data) == meta["sha256"] else "modified"),
        }
    manifest_ok = _seal(body) == custody.get("manifest_sha256")
    return {
        "manifest_ok": manifest_ok,
        "verified": manifest_ok and all(r["status"] == "ok" for r in results.values()),
        "files": results,
    }
