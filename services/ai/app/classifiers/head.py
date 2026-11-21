"""Lightweight per-module classification head on top of embeddings (ADR-0011):
logistic regression + isotonic calibration, trained in seconds on CPU from
weak-supervision / analyst labels. Falls back to a topic-vs-noise contrast score
before the first training run, so M1/M2/M3 produce scores from day one.
"""
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression

MODEL_DIR = Path("/app/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def _model_path(module: str) -> Path:
    return MODEL_DIR / f"{module}_head.joblib"


def _version_path(module: str) -> Path:
    return MODEL_DIR / f"{module}_version.json"


def load_head(module: str):
    path = _model_path(module)
    if path.exists():
        return joblib.load(path)
    return None


def get_model_version(module: str) -> int:
    path = _version_path(module)
    if path.exists():
        return json.loads(path.read_text()).get("version", 1)
    return 1


CONTRAST_SLOPE = 60.0


def contrast_score(vec: np.ndarray, positive: np.ndarray, negative: np.ndarray | None) -> float:
    """Sigmoid of how much closer the text is to the best topic phrase than to the best
    off-topic phrase. Embeddings are normalized, so a dot product is the cosine."""
    closest_topic = float(np.max(positive @ vec))
    closest_noise = float(np.max(negative @ vec)) if negative is not None else 0.0
    return float(1 / (1 + np.exp(-CONTRAST_SLOPE * (closest_topic - closest_noise))))


def score_with_fallback(
    module: str, embedding: list[float], topic_vectors: tuple[np.ndarray, np.ndarray | None] | None
) -> float:
    head = load_head(module)
    vec = np.array(embedding)

    if head is not None:
        return float(head.predict_proba(vec.reshape(1, -1))[0][1])

    if topic_vectors is not None:
        return contrast_score(vec, *topic_vectors)

    return 0.1


def train_head(module: str, embeddings: list[list[float]], labels: list[bool]) -> dict:
    if len(set(labels)) < 2 or len(labels) < 10:
        return {"status": "skipped", "reason": "not enough labeled data (need >=10 rows, both classes)"}

    X = np.array(embeddings)
    y = np.array([1 if label else 0 for label in labels])

    base = LogisticRegression(max_iter=1000)
    calibrated = CalibratedClassifierCV(base, method="isotonic", cv=min(5, max(2, len(labels) // 5)))
    calibrated.fit(X, y)

    joblib.dump(calibrated, _model_path(module))
    version = get_model_version(module) + 1
    _version_path(module).write_text(json.dumps({"version": version}))

    return {"status": "trained", "version": version, "n_samples": len(labels)}
