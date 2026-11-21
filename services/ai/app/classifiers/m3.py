"""M3 - shadow advisory: unauthorized entities offering advisory-like services,
plus clone-firm / lookalike-domain detection against the registry (ADR-0004).
"""
import re
from urllib.parse import urlparse

from investwatch_common.models import Entity
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

ADVISORY_PATTERNS = [
    r"doradztwo inwestycyjne",
    r"zarz(a|ą)dzanie maj(a|ą)tkiem",
    r"family office",
    r"sygnały inwestycyjne",
    r"portfel modelowy",
    r"gwarantowany zysk",
]

LOOKALIKE_THRESHOLD = 80


def detect_advisory_offer(text: str) -> list[str]:
    evidence = []
    for pattern in ADVISORY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            evidence.append(match.group(0))
    return evidence


def detect_lookalike_domain(db: Session, url: str) -> dict | None:
    """Compares the document's domain against every authorized entity's known
    domains; a high string-similarity, non-exact match suggests a clone site."""
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if not domain:
        return None

    authorized_entities = db.query(Entity).filter(Entity.authorized.is_(True)).all()
    best: tuple[str, str, int] | None = None

    for entity in authorized_entities:
        for known_domain in entity.domains or []:
            if known_domain == domain:
                return None  # exact match, not a lookalike
            score = fuzz.ratio(known_domain, domain)
            if score >= LOOKALIKE_THRESHOLD and (best is None or score > best[2]):
                best = (entity.name, known_domain, score)

    if best is None:
        return None
    return {
        "suspected_domain": domain,
        "mimics_entity": best[0],
        "mimics_domain": best[1],
        "similarity": best[2],
    }


def build_details(db: Session, text: str, url: str) -> dict:
    advisory_evidence = detect_advisory_offer(text)
    lookalike = detect_lookalike_domain(db, url)
    return {
        "advisory_offer_evidence": advisory_evidence,
        "lookalike_domain": lookalike,
        "domain": lookalike["suspected_domain"] if lookalike else urlparse(url).netloc,
    }
