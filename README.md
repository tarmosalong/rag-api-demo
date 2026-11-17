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

Järgmised sammud: RAG tuum (`src/ingest.py`, `src/rag.py`), FastAPI `/v1`, Docker, CI — vt projekti plaani.

## Konfiguratsioon

Kõik seaded on `.env.example` kommentaaridega; saladused ainult lokaalses `.env` failis.