# rag-api-demo

Production-style **RAG API** demo: FastAPI, local Chroma, xAI Grok embeddings + chat, citations and usage metrics.

## Samm 0 — käivitus

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # lisa XAI_API_KEY; commiti .env mitte kunagi
make lint && make test
```

Kaustad: `src/`, `tests/`, `data/raw/` (näidiskorpus), `scripts/`, `docs/`, `.github/workflows/`.

Järgmised sammud: RAG tuum (`src/ingest.py`, `src/rag.py`), FastAPI `/v1`, Docker, CI — vt projekti plaani.

## Konfiguratsioon

Kõik seaded on `.env.example` kommentaaridega; saladused ainult lokaalses `.env` failis.