"""Request/response schemas for the api service."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class EntityOut(BaseModel):
    id: int
    name: str
    type: str | None
    authorized: bool | None
    source: str | None
    domains: list[str] | None

    class Config:
        from_attributes = True


class FindingOut(BaseModel):
    id: int
    document_id: int
    module: str
    score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FindingDetail(FindingOut):
    model_version: int
    prompt_version: int
    evidence: str | None
    explanation: str | None
    details: dict[str, Any]
    document_url: str
    document_title: str | None
    document_platform: str | None
    screenshot_url: str | None = None

    class Config:
        from_attributes = True


class FindingStatusUpdate(BaseModel):
    status: str  # in_review, confirmed, dismissed, escalated


class CaseOut(BaseModel):
    id: int
    primary_entity_id: int
    finding_ids: list[int] | None
    description: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CalibrationMetrics(BaseModel):
    module: str
    threshold: float
    precision: float
    recall: float
    false_positives: int
    false_negatives: int
    pr_curve: list[dict[str, float]]


class ScanRequest(BaseModel):
    url: str


class PipelineStageEvent(BaseModel):
    scan_id: str
    stage: str  # fetch, preprocess, embed, classify, llm, done, error
    status: str  # running, done, error
    message: str | None = None
    data: dict[str, Any] = {}
