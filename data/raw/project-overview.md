# rag-api-demo — project overview

This repo is a **production slice** RAG API demo: FastAPI `/v1`, local Chroma index,
xAI Grok embeddings and chat, citations, and token/latency metrics.

## Goal

Show employers a versioned API, tests and CI, Docker, and cost-aware design
(`MAX_OUTPUT_TOKENS`, ingest embed-cache) without reasoning models or live xAI in CI.

## Corpus facts (this file)

- Project name: **rag-api-demo**
- Vector store: **Chroma** (`data/chroma/`)
- Embedding model: **grok-embedding-small**
- Chat model: **grok-3-fast-latest** (configurable via `.env`)