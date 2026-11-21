"""Entity resolution: matches text mentions against the registry (ADR-0004)
by alias (fuzzy) and by domain found in the document URL. Results are cached
in Redis as `wzmianka -> entity_id | null` per the caching strategy (ADR-0005).
"""
import json
from urllib.parse import urlparse

from investwatch_common.models import Entity, EntityAlias
from investwatch_common.redis_client import get_redis
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

FUZZY_THRESHOLD = 85
CACHE_PREFIX = "entity_resolution:"
CACHE_TTL_SECONDS = 3600


def resolve_by_domain(db: Session, url: str) -> Entity | None:
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if not domain:
        return None
    return db.query(Entity).filter(Entity.domains.any(domain)).first()


def resolve_mention(db: Session, text: str) -> Entity | None:
    cache_key = f"{CACHE_PREFIX}{text.lower()[:200]}"
    redis_client = get_redis()
    cached = redis_client.get(cache_key)
    if cached is not None:
        payload = json.loads(cached)
        return db.get(Entity, payload["entity_id"]) if payload.get("entity_id") else None

    text_lower = text.lower()
    best_match: tuple[Entity, int] | None = None

    aliases = db.query(EntityAlias).all()
    for alias in aliases:
        score = fuzz.partial_ratio(alias.alias.lower(), text_lower)
        if score >= FUZZY_THRESHOLD and (best_match is None or score > best_match[1]):
            best_match = (alias.entity, score)

    entity = best_match[0] if best_match else None
    cache_payload = json.dumps({"entity_id": entity.id if entity else None})
    redis_client.set(cache_key, cache_payload, ex=CACHE_TTL_SECONDS)
    return entity
