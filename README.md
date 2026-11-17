# rag-api-demo

Production-style **RAG API** demo: FastAPI, local Chroma, xAI Grok embeddings + chat, citations and usage metrics.

## Samm 0 — käivitus

```bash
cp .env.example .env   # XAI võti hiljem (samm 1+); .env mitte commiti
make install           # .venv kui võimalik, muidu pip install
make lint && make test # oodatav: All checks passed + 2 passed
```

**Windows (PowerShell):** `copy .env.example .env`, siis `python -m venv .venv`, `.\.venv\Scripts\activate`, `pip install -r requirements.txt`. Kui `make test` ei tööta, kasuta `$env:RAG_OFFLINE="1"; python -m pytest -q`.

Kaustad: `src/`, `tests/`, `data/raw/` (näidiskorpus), `scripts/`, `docs/`, `.github/workflows/`.

## Live RAG (vajab võtit)

```bash
cp .env.example .env   # pane päris XAI_API_KEY, RAG_OFFLINE=0
make ingest
make dev               # http://127.0.0.1:8765/docs
```

API: `GET /health`, `GET /v1/stats`, `POST /v1/ask`, `POST /v1/upload` (max 5 MB).

Docker: `make docker` (enne ingest hostis või konteineris).

## Konfiguratsioon

Kõik seaded on `.env.example` kommentaaridega; saladused ainult lokaalses `.env` failis.