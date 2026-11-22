"""Messages passed between scraper-worker, ai-worker and api over Celery/Redis."""
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class RawDocument(BaseModel):
    """Output of a Collector. Common shape for every source plugin."""

    source_name: str
    url: str
    canonical_url: str | None = None
    platform: str
    author: str | None = None
    title: str | None = None
    published_at: datetime | None = None
    content: str
    html: str | None = None
    screenshot_png: bytes | None = None
    device_screenshots: dict[str, bytes] = {}
    computed_styles: dict[str, Any] | None = None
    extra: dict[str, Any] = {}


class ClassifierResult(BaseModel):
    module: str  # m1, m2, m3
    score: float
    model_version: int
    details: dict[str, Any] = {}


def _as_text_list(value: Any) -> list[str]:
    """LLMs sometimes return a bare string, numbers or objects where a list of strings is expected."""
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    texts = []
    for item in items:
        if isinstance(item, dict):
            item = item.get("text") or item.get("name") or item.get("quote") or json.dumps(item, ensure_ascii=False)
        if item not in (None, ""):
            texts.append(str(item))
    return texts


class LLMAnalysis(BaseModel):
    entities: list[str] = []
    profit_claims: list[str] = []
    risk_statements: list[str] = []
    verdict: str
    rationale: str

    @field_validator("entities", "profit_claims", "risk_statements", mode="before")
    @classmethod
    def _coerce_lists(cls, value: Any) -> list[str]:
        return _as_text_list(value)

    @field_validator("verdict", "rationale", mode="before")
    @classmethod
    def _coerce_text(cls, value: Any) -> str:
        return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


class FindingPayload(BaseModel):
    document_id: int
    module: str
    score: float
    model_version: int
    prompt_version: int
    evidence: str
    explanation: str
    details: dict[str, Any] = {}
