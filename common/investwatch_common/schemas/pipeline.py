"""Messages passed between scraper-worker, ai-worker and api over Celery/Redis."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


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
    computed_styles: dict[str, Any] | None = None
    extra: dict[str, Any] = {}


class ClassifierResult(BaseModel):
    module: str  # m1, m2, m3
    score: float
    model_version: int
    details: dict[str, Any] = {}


class LLMAnalysis(BaseModel):
    entities: list[str] = []
    profit_claims: list[str] = []
    risk_statements: list[str] = []
    verdict: str
    rationale: str


class FindingPayload(BaseModel):
    document_id: int
    module: str
    score: float
    model_version: int
    prompt_version: int
    evidence: str
    explanation: str
    details: dict[str, Any] = {}
