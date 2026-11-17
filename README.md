# rag-api-demo

Production-style **RAG API** demo: FastAPI, local Chroma, xAI Grok embeddings + chat, citations and usage metrics.

[![CI](https://github.com/tarmosalong/rag-api-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/tarmosalong/rag-api-demo/actions/workflows/ci.yml)

## Quick start (scaffold)

```bash
cp .env.example .env   # add XAI_API_KEY later; never commit .env
make install
make lint && make test # expect: All checks passed + tests passing
```

**Windows (PowerShell):** `copy .env.example .env`, then `python -m venv .venv`, `.\.venv\Scripts\activate`, `pip install -r requirements.txt`. If `make test` fails, use `$env:RAG_OFFLINE="1"; python -m pytest -q`.

Layout: `src/`, `tests/`, `data/raw/` (sample corpus), `scripts/`, `docs/`, `.github/workflows/`.

## Live RAG (requires API key)

```bash
cp .env.example .env   # set XAI_API_KEY, RAG_OFFLINE=0
make ingest
make dev               # http://127.0.0.1:8765/docs
```

Endpoints: `GET /health`, `GET /v1/stats`, `POST /v1/ask`, `POST /v1/upload` (max 5 MB).

Docker: `make docker` (run ingest on the host or in the container first).

## Configuration

Settings are documented in `.env.example`; secrets live only in local `.env`.

## Contributing

Repository content is English only — see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).