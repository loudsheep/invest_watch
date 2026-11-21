"""Ingests sample documents from the hackathon USB-drive dataset (placed in data/dataset/)
through the same pipeline as live collectors. Expected shape per ADR-0003: one JSON file
per document, or a single documents.jsonl - whichever the organizers actually hand over.
Until the real format is known, this collector reads either shape from data/dataset/.
"""
import json
from collections.abc import Iterator
from pathlib import Path

from investwatch_common.schemas import RawDocument

from .base import Collector

DATASET_DIR = Path("/app/data/dataset")


class DatasetCollector(Collector):
    name = "dataset"

    def discover(self) -> Iterator[str]:
        if not DATASET_DIR.exists():
            return
        jsonl = DATASET_DIR / "documents.jsonl"
        if jsonl.exists():
            with jsonl.open(encoding="utf-8") as f:
                for i, _ in enumerate(f):
                    yield f"documents.jsonl:{i}"
            return
        for path in sorted(DATASET_DIR.glob("*.json")):
            yield path.name

    def fetch(self, candidate: str) -> RawDocument | None:
        if candidate.startswith("documents.jsonl:"):
            idx = int(candidate.split(":", 1)[1])
            with (DATASET_DIR / "documents.jsonl").open(encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i == idx:
                        return self._to_raw_document(json.loads(line))
            return None

        path = DATASET_DIR / candidate
        if not path.exists():
            return None
        return self._to_raw_document(json.loads(path.read_text(encoding="utf-8")))

    @staticmethod
    def _to_raw_document(raw: dict) -> RawDocument:
        return RawDocument(
            source_name="dataset",
            url=raw.get("url") or f"dataset://{raw.get('id', 'unknown')}",
            platform=raw.get("platform", "dataset"),
            author=raw.get("author"),
            title=raw.get("title"),
            published_at=raw.get("published_at"),
            content=raw.get("content", ""),
            html=raw.get("html"),
            extra={"original_id": raw.get("id"), "labeled": raw.get("label")},
        )
