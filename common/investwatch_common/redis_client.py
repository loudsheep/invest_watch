import redis

from .config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


HIGH_RISK_CHANNEL = "findings:high_risk"
RAW_DOCUMENTS_QUEUE = "raw_documents"
FINDINGS_QUEUE = "findings"
PROXY_FAILURES_KEY = "proxy:failures"
PROXY_CIRCUIT_KEY = "proxy:circuit_open_until"
