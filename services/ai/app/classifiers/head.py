"""Lightweight per-module classification head on top of embeddings (ADR-0011):
logistic regression + isotonic calibration, trained in seconds on CPU from
weak-supervision / analyst labels. Falls back to a cosine-similarity-to-topic
heuristic before the first training run, so M1/M2/M3 produce scores from day one.
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


def score_with_fallback(module: str, embedding: list[float], topic_centroid: list[float] | None) -> float:
    head = load_head(module)
    vec = np.array(embedding).reshape(1, -1)

    if head is not None:
        proba = head.predict_proba(vec)[0][1]
        return float(proba)

    if topic_centroid is not None:
        centroid = np.array(topic_centroid)
        cosine = float(np.dot(vec[0], centroid) / (np.linalg.norm(vec[0]) * np.linalg.norm(centroid) + 1e-9))
        # Map cosine similarity [-1, 1] to a rough probability-like score.
        return max(0.0, min(1.0, (cosine + 1) / 2))

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
