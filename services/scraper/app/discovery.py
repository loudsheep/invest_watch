"""Builds per-collector discovery config from config/taxonomies.yaml and the
entity registry, so sources need no hand-maintained query lists."""
from pathlib import Path

import yaml
from investwatch_common.models import Entity

TAXONOMIES_PATH = Path("/app/config/taxonomies.yaml")
DISCOVERY_SECTIONS = ("m1_finfluencer", "m2_risk_disclosure", "m3_shadow_advisory")


def discovery_config(db) -> dict:
    queries: list[str] = []
    if TAXONOMIES_PATH.exists():
        taxonomies = yaml.safe_load(TAXONOMIES_PATH.read_text(encoding="utf-8")) or {}
        for section in DISCOVERY_SECTIONS:
            queries += (taxonomies.get(section) or {}).get("discovery_queries") or []
        seed_channels = (taxonomies.get("m1_finfluencer") or {}).get("seed_channels") or []
        seed_profiles = (taxonomies.get("m1_finfluencer") or {}).get("seed_profiles") or []
    else:
        seed_channels, seed_profiles = [], []

    registry_domains = [
        domain
        for (domains,) in db.query(Entity.domains).filter(Entity.authorized.is_(True)).all()
        for domain in domains or []
    ]
    return {
        "queries": queries,
        "search_terms": queries,
        "seed_urls": [f"https://{domain}" for domain in registry_domains],
        "seed_channels": seed_channels,
        "seed_profiles": seed_profiles,
    }
