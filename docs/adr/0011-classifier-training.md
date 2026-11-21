# 0011. Classifier training via weak supervision and LLM distillation

- Status: Accepted
- Date: 2026-11-21

## Context

No labeled data exists at the start. The threshold is only meaningful if classifier scores are calibrated probabilities. There is no GPU available inside Docker on macOS.

## Considered options

1. Zero-shot embedding similarity. No training, weak accuracy, uncalibrated scores.
2. Fine-tuning HerBERT. Best accuracy, needs hundreds of clean labels and GPU time.
3. Weak supervision plus LLM distillation into a lightweight head.

## Decision

Option 3:

1. Rules and the LLM (offline, one-off) label a few hundred documents from the dataset and the first crawl.
2. A logistic regression head per module is trained on `multilingual-e5` embeddings, in seconds on CPU.
3. Probabilities are calibrated (isotonic or Platt).
4. Analyst labels from the dashboard are added to the training set; a "Retrain" action in the calibration panel trains a new version and bumps `model_version`.

## Consequences

- Scores are interpretable and the threshold maps to a real precision-recall trade-off.
- The system improves with use (active learning with a human in the loop).
