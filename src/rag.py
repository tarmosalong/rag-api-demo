import logging
import time

from src.chroma_store import get_collection
from src.config import Settings, get_settings
from src.embed_cache import EmbedCache
from src.schemas import RagResult, SourceCitation, TokenUsage
from src.xai_client import embed_texts, get_openai_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Answer only using the context below. "
    "If the answer is not in the context, say clearly that you do not know."
)

OFFLINE_ANSWER = (
    "Offline mode: mock answer for RAG API contract tests. "
    "For live answers, set RAG_OFFLINE=0 and run ingest."
)


def offline_rag_result() -> RagResult:
    return RagResult(
        answer=OFFLINE_ANSWER,
        sources=[
            SourceCitation(
                source="operations-handbook.txt",
                chunk_id="operations-handbook:0",
                doc_id="operations-handbook",
                score=1.0,
                snippet="Offline mode: RAG_OFFLINE=1",
            )
        ],
        usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        latency_ms=0.0,
    )


def _build_context(chunks: list[str], settings: Settings) -> str:
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        if total + len(chunk) + 2 > settings.max_context_chars:
            break
        parts.append(chunk)
        total += len(chunk) + 2
    return "\n\n".join(parts)


def answer(question: str, settings: Settings | None = None) -> RagResult:
    s = settings or get_settings()
    started = time.perf_counter()

    if s.rag_offline:
        result = offline_rag_result()
        result.latency_ms = (time.perf_counter() - started) * 1000
        return result

    collection = get_collection(s)
    if collection.count() == 0:
        raise RuntimeError("index is empty; run ingest first")

    query_vector = embed_texts([question], s)[0]
    hits = collection.query(
        query_embeddings=[query_vector],
        n_results=s.top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = (hits.get("documents") or [[]])[0]
    metadatas = (hits.get("metadatas") or [[]])[0]
    distances = (hits.get("distances") or [[]])[0]

    sources: list[SourceCitation] = []
    for doc, meta, dist in zip(documents, metadatas, distances, strict=True):
        snippet = (doc or "")[:240]
        score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
        sources.append(
            SourceCitation(
                source=meta.get("source", ""),
                chunk_id=meta.get("chunk_id", ""),
                doc_id=meta.get("doc_id", ""),
                score=round(score, 4),
                snippet=snippet,
            )
        )

    context = _build_context(documents, s)
    client = get_openai_client(s)
    completion = client.chat.completions.create(
        model=s.chat_model,
        max_tokens=s.max_output_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )

    usage_raw = completion.usage
    usage = TokenUsage(
        prompt_tokens=usage_raw.prompt_tokens if usage_raw else 0,
        completion_tokens=usage_raw.completion_tokens if usage_raw else 0,
        total_tokens=usage_raw.total_tokens if usage_raw else 0,
    )
    text = completion.choices[0].message.content or ""

    latency_ms = (time.perf_counter() - started) * 1000
    return RagResult(
        answer=text.strip(),
        sources=sources,
        usage=usage,
        latency_ms=round(latency_ms, 2),
    )


def get_stats(settings: Settings | None = None) -> tuple[int, int, str | None]:
    from src.chroma_store import index_stats

    s = settings or get_settings()
    docs, chunks = index_stats(s)
    cache = EmbedCache(s.embed_cache_path)
    last = cache.get_last_ingest_at()
    cache.close()
    return docs, chunks, last