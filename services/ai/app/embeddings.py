"""Embeddings model: intfloat/multilingual-e5-base (ADR-0011).
Loaded once per worker process - model load is the expensive part, not inference.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-base"


@lru_cache
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> list[float]:
    model = get_model()
    # e5 models expect a "query: " / "passage: " prefix for best retrieval quality.
    vector = model.encode(f"passage: {text}", normalize_embeddings=True)
    return vector.tolist()
