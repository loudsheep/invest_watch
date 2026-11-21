"""Precomputes one embedding centroid per module from config/taxonomies.yaml,
used by the classifier head as a cold-start fallback before any training run.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml

from .embeddings import embed

TAXONOMY_PATH = Path("/app/config/taxonomies.yaml")

MODULE_KEY_MAP = {"m1": "m1_finfluencer", "m2": "m2_risk_disclosure", "m3": "m3_shadow_advisory"}


@lru_cache
def get_centroid(module: str) -> list[float] | None:
    taxonomy = yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))
    key = MODULE_KEY_MAP.get(module)
    phrases = (taxonomy.get(key) or {}).get("topic_phrases", [])
    if not phrases:
        return None
    vectors = [embed(phrase) for phrase in phrases]
    centroid = np.mean(vectors, axis=0)
    return centroid.tolist()
