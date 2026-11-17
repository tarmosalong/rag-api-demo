# rag-api-demo — projekti ülevaade

See repos on **production slice** RAG API demonstratsioon: FastAPI `/v1`, kohalik Chroma indeks,
xAI Grok embeddingud ja chat, tsiteeringud ning tokeni/latentsuse mõõdikud.

## Eesmärk

Näidata tööandjale versioonitud API-d, testide ja CI põhjat, Dockerit ja kuluteadlikku disaini
(MAX_OUTPUT_TOKENS, embed-cache ingestil) ilma reasoning-mudelite ja live CI API-kuluta.

## Korpus sellest failist

- Projekti nimi: **rag-api-demo**
- Vektorindeks: **Chroma** (`data/chroma/`)
- Embedding mudel: **grok-embedding-small**
- Chat mudel: **grok-3-fast-latest** (konfigureeritav `.env` kaudu)