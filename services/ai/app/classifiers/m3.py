"""M3 - shadow advisory: unauthorized entities offering advisory-like services,
plus clone-firm / lookalike-domain detection against the registry (ADR-0004).
"""
import re
import socket
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from investwatch_common.models import Entity
from investwatch_common.redis_client import get_redis
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from ..entity_resolution import find_entities_by_ids

ADVISORY_PATTERNS = [
    r"doradztwo inwestycyjne",
    r"zarz(a|ą)dzanie maj(a|ą)tkiem",
    r"family office",
    r"sygnały inwestycyjne",
    r"portfel modelowy",
    r"gwarantowany zysk",
]

LOOKALIKE_THRESHOLD = 80
RDAP_URL = "https://rdap.org/domain/"
DOMAIN_AGE_CACHE_SECONDS = 86400 * 7
UNKNOWN_AGE = "unknown"


WHOIS_PORT = 43
WHOIS_TIMEOUT_SECONDS = 5
SECOND_LEVEL_LABELS = {"co", "com", "org", "net", "gov", "ac"}
CREATED_RE = re.compile(r"^\s*(?:created|creation date|registered on|registration time)\s*:\s*(.+?)\s*$", re.I | re.M)
DATE_FORMATS = ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%b-%Y", "%Y.%m.%d")


def registered_domain(hostname: str) -> str:
    labels = hostname.lower().split(".")
    if len(labels) >= 3 and labels[-2] in SECOND_LEVEL_LABELS:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def _whois(server: str, query: str) -> str:
    with socket.create_connection((server, WHOIS_PORT), timeout=WHOIS_TIMEOUT_SECONDS) as sock:
        sock.sendall(f"{query}\r\n".encode())
        chunks = []
        while chunk := sock.recv(4096):
            chunks.append(chunk)
    return b"".join(chunks).decode("utf-8", "ignore")


def _parse_date(value: str) -> datetime | None:
    value = value.strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _age_from_rdap(domain: str) -> int | None:
    response = httpx.get(f"{RDAP_URL}{domain}", timeout=4, follow_redirects=True)
    response.raise_for_status()
    for event in response.json().get("events", []):
        if event.get("eventAction") == "registration":
            registered = datetime.fromisoformat(event["eventDate"].replace("Z", "+00:00"))
            return (datetime.now(UTC) - registered).days
    return None


def _age_from_whois(domain: str) -> int | None:
    tld = domain.rsplit(".", 1)[-1]
    referral = re.search(r"^\s*(?:refer|whois):\s*(\S+)", _whois("whois.iana.org", tld), re.I | re.M)
    if referral is None:
        return None
    match = CREATED_RE.search(_whois(referral.group(1), domain))
    created = _parse_date(match.group(1)) if match else None
    return (datetime.now(UTC).replace(tzinfo=None) - created).days if created else None


def domain_age_days(hostname: str) -> int | None:
    """Domain age from RDAP, falling back to WHOIS (many ccTLDs, including .pl, have no RDAP);
    None when it cannot be determined."""
    if "." not in hostname:
        return None
    domain = registered_domain(hostname)
    cache_key = f"domain_age:{domain}"
    redis_client = get_redis()
    cached = redis_client.get(cache_key)
    if cached is not None:
        return None if cached == UNKNOWN_AGE else int(cached)

    age: int | None = None
    for lookup in (_age_from_rdap, _age_from_whois):
        try:
            age = lookup(domain)
        except (httpx.HTTPError, OSError, ValueError, KeyError):
            age = None
        if age is not None:
            break
    redis_client.set(cache_key, UNKNOWN_AGE if age is None else age, ex=DOMAIN_AGE_CACHE_SECONDS)
    return age


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
    domain = (urlparse(url).hostname or "").lower().removeprefix("www.")
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
    hostname = urlparse(url).hostname or ""
    id_matches = [
        {
            "id_type": kind,
            "number": number,
            "entity": entity.name,
            "authorized": bool(entity.authorized),
            "source": entity.source,
        }
        for kind, number, entity in find_entities_by_ids(db, text)
    ]
    return {
        "registry_id_matches": id_matches,
        "advisory_offer_evidence": advisory_evidence,
        "lookalike_domain": lookalike,
        "domain": lookalike["suspected_domain"] if lookalike else urlparse(url).netloc,
        "domain_age_days": domain_age_days(hostname) if advisory_evidence or lookalike else None,
    }
