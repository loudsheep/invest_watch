# 0014. Embedding and LLM model selection

- Status: Accepted
- Date: 2026-11-21

## Context

About 20 GB of RAM is realistically available for models on the reference machine after the rest of the stack. The specification mentions Gemma and BERT-style classifiers. Winners transfer copyright to UKNF, so model licenses matter.

## Decision

- Embeddings: `intfloat/multilingual-e5-base` (MIT, good Polish support, fast on CPU). Downloaded at `ai` image build time so it works offline.
- LLM: latest available Gemma via Ollama, around 12B at Q4 for the demo via native Ollama (Metal), around 4B as the default inside the container. Configured via `LLM_MODEL`.
- Structured output: Ollama `format: json`, Pydantic validation and retry.
- An `ollama-init` container pulls the model on first start.
- Apache 2.0 alternatives (Qwen, Mistral) are swappable via `.env`; the Gemma terms of use are documented in the README.

## Consequences

- The model choice is a configuration concern, not a code change.
- License implications are documented for the copyright transfer.
