# rag-api-demo — project overview

HTTP API for retrieval-augmented generation: FastAPI `/v1`, local Chroma index,
xAI Grok embeddings and chat, citations, and token/latency metrics.

## Scope

Versioned REST surface, tests and CI, container packaging, and cost guardrails
(`MAX_OUTPUT_TOKENS`, ingest embed-cache) without reasoning models or live xAI in CI.

## Corpus facts (this file)

- Project name: **rag-api-demo**
- Vector store: **Chroma** (`data/chroma/`)
- Embedding model: **grok-embedding-small**
- Chat model: **grok-3-fast-latest** (configurable via `.env`)