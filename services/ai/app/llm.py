"""OpenAI-compatible chat client (OpenRouter or Ollama /v1) for candidate documents
that cleared the pre-filter threshold.
Structured output (response_format=json_object) + Pydantic validation + one retry on parse
failure, per CONCEPT ch.5 / ADR-0002 / ADR-0014.
"""
import json

import httpx
from investwatch_common.config import settings
from investwatch_common.logging import get_logger
from investwatch_common.schemas import LLMAnalysis

logger = get_logger(__name__)

PROMPT_VERSION = 1

SYSTEM_PROMPT = (
    "You are a compliance analyst assistant for the Polish financial regulator (UKNF). "
    "Analyze the given text, written in Polish, and extract: mentioned entities, "
    "profit/return claims, risk statements, a verdict (one short phrase) and a rationale "
    "(1-3 sentences). Quote the original Polish text for claims/statements. "
    "Respond with ONLY a JSON object matching this schema: "
    '{"entities": [string], "profit_claims": [string], "risk_statements": [string], '
    '"verdict": string, "rationale": string}'
)


def _call_llm(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"} if settings.llm_api_key else {}
    response = httpx.post(
        f"{settings.llm_base_url.rstrip('/')}/chat/completions",
        headers=headers,
        json={
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def analyze(text: str, module: str) -> LLMAnalysis | None:
    prompt = f"Module: {module}\n\nText:\n{text[:4000]}"

    for attempt in range(2):
        try:
            raw = _call_llm(prompt)
            data = json.loads(raw)
            return LLMAnalysis(**data)
        except (httpx.HTTPError, json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("llm_analysis_failed", attempt=attempt, error=str(exc))
    return None
