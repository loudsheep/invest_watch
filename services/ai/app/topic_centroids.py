"""Embeds the topic and negative phrases from config/taxonomies.yaml, used by the
classifier head as a cold-start fallback before any training run.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml

from .embeddings import embed

TAXONOMY_PATH = Path("/app/config/taxonomies.yaml")

MODULE_KEY_MAP = {"m1": "m1_finfluencer", "m2": "m2_risk_disclosure", "m3": "m3_shadow_advisory"}


@lru_cache
def _taxonomy() -> dict:
    return yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))


def _embed_all(phrases: list[str]) -> np.ndarray | None:
    return np.array([embed(p) for p in phrases]) if phrases else None


@lru_cache
def get_topic_vectors(module: str) -> tuple[np.ndarray, np.ndarray | None] | None:
    """(topic phrase vectors, negative phrase vectors or None) for a module."""
    taxonomy = _taxonomy()
    positive = _embed_all((taxonomy.get(MODULE_KEY_MAP.get(module)) or {}).get("topic_phrases", []))
    if positive is None:
        return None
    return positive, _embed_all(taxonomy.get("negative_phrases", []))
