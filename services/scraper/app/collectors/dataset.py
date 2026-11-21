"""Ingests a labeled or unlabeled document dataset (the hackathon USB-drive samples) from
data/dataset/ through the same pipeline as live collectors.

Accepted files, any mix: `*.jsonl` (one object per line), `*.json` (an object or an array),
`*.csv` (header row). Field names are matched case-insensitively through FIELD_ALIASES, so a
different export only needs a new alias. An optional `label` (true/false, or an object like
{"m1": true, "m2": false}) becomes the analyst ground truth for calibration.
"""
import csv
import json
from collections.abc import Iterator
from pathlib import Path

from investwatch_common.logging import get_logger
from investwatch_common.schemas import RawDocument

from .base import Collector

logger = get_logger(__name__)

DATASET_DIR = Path("/app/data/dataset")

FIELD_ALIASES = {
    "url": ("url", "link", "adres", "href"),
    "content": ("content", "text", "body", "tekst", "tresc", "treść", "description", "opis"),
    "title": ("title", "tytul", "tytuł", "headline"),
    "author": ("author", "autor", "channel", "uploader", "account"),
    "platform": ("platform", "source", "zrodlo", "źródło", "network"),
    "published_at": ("published_at", "date", "data", "created_at", "timestamp"),
    "html": ("html",),
    "label": ("label", "etykieta", "ground_truth", "violation", "naruszenie"),
    "id": ("id", "uuid", "doc_id"),
}


def _pick(record: dict, field: str):
    lowered = {str(k).lower(): v for k, v in record.items()}
    for alias in FIELD_ALIASES[field]:
        if alias in lowered and lowered[alias] not in (None, ""):
            return lowered[alias]
    return None


def _parse_label(value):
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("true", "1", "yes", "tak"):
            return True
        if text in ("false", "0", "no", "nie"):
            return False
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def _read_file(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else [data]
    if path.suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    return []


class DatasetCollector(Collector):
    name = "dataset"

    def __init__(self, config: dict):
        super().__init__(config)
        self._records: list[tuple[str, dict]] = []

    def discover(self) -> Iterator[str]:
        self._records = []
        if not DATASET_DIR.exists():
            return
        for path in sorted(DATASET_DIR.iterdir()):
            try:
                records = _read_file(path)
            except (OSError, ValueError) as exc:
                logger.warning("dataset_file_unreadable", file=path.name, error=str(exc))
                continue
            self._records += [(f"{path.name}#{i}", record) for i, record in enumerate(records)]
        for index in range(len(self._records)):
            yield str(index)

    def fetch(self, candidate: str) -> RawDocument | None:
        key, record = self._records[int(candidate)]
        content = _pick(record, "content")
        if not content and not _pick(record, "html"):
            logger.warning("dataset_record_without_content", record=key)
            return None
        return RawDocument(
            source_name="dataset",
            url=_pick(record, "url") or f"dataset://{_pick(record, 'id') or key}",
            platform=str(_pick(record, "platform") or "dataset"),
            author=_pick(record, "author"),
            title=_pick(record, "title"),
            published_at=_pick(record, "published_at"),
            content=str(content or ""),
            html=_pick(record, "html"),
            extra={"label": _parse_label(_pick(record, "label")), "record": key},
        )
