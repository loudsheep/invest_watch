"""Entity resolution: matches text mentions against the registry (ADR-0004)
by alias (fuzzy) and by domain found in the document URL. Results are cached
in Redis as `wzmianka -> entity_id | null` per the caching strategy (ADR-0005).
"""
import json
import re
from urllib.parse import urlparse

from investwatch_common.models import Entity, EntityAlias
from investwatch_common.redis_client import get_redis
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

FUZZY_THRESHOLD = 85
CACHE_PREFIX = "entity_resolution:"
CACHE_TTL_SECONDS = 3600


def resolve_by_domain(db: Session, url: str) -> Entity | None:
    domain = (urlparse(url).hostname or "").lower().removeprefix("www.")
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


KRS_RE = re.compile(r"\bKRS\s*(?:nr\.?|numer)?[:\s]*(\d{10})\b", re.IGNORECASE)
NIP_RE = re.compile(r"\bNIP\s*(?:nr\.?|numer)?[:\s]*((?:PL)?[\d\- ]{10,14})", re.IGNORECASE)


def extract_registry_ids(text: str) -> dict[str, set[str]]:
    """KRS and NIP numbers quoted in the text, digits only."""
    nips = {digits for m in NIP_RE.finditer(text) if len(digits := re.sub(r"\D", "", m.group(1))) == 10}
    return {"krs": {m.group(1) for m in KRS_RE.finditer(text)}, "nip": nips}


def find_entities_by_ids(db: Session, text: str) -> list[tuple[str, str, Entity]]:
    """Registry entities whose KRS or NIP appears in the text: (id type, number, entity)."""
    ids = extract_registry_ids(text)
    matches = []
    if ids["krs"]:
        matches += [("KRS", e.krs, e) for e in db.query(Entity).filter(Entity.krs.in_(ids["krs"])).all()]
    if ids["nip"]:
        matches += [("NIP", e.nip, e) for e in db.query(Entity).filter(Entity.nip.in_(ids["nip"])).all()]
    return matches


def find_entities_in_text(db: Session, text: str) -> list[Entity]:
    """Registry entities whose name or alias appears verbatim (whole words) in the text."""
    found: dict[int, Entity] = {}
    for alias in db.query(EntityAlias).all():
        if alias.entity_id not in found and re.search(rf"\b{re.escape(alias.alias)}\b", text, re.IGNORECASE):
            found[alias.entity_id] = alias.entity
    return list(found.values())
