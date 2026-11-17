import logging
import re
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

OFFLINE_MOCK_ANSWER = (
    "Offline mode: mock answer for RAG API contract tests. "
    "For live answers, set RAG_OFFLINE=0 and run ingest."
)

_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "do",
        "does",
        "for",
        "how",
        "is",
        "it",
        "one",
        "the",
        "to",
        "what",
        "when",
        "which",
        "who",
        "you",
        "your",
        "run",
        "use",
        "used",
    }
)


def _question_terms(question: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9_]+", question.lower())
    return [w for w in words if w not in _STOP_WORDS and len(w) > 1]


def _keyword_score(text: str, terms: list[str]) -> float:
    if not terms or not text:
        return 0.0
    lower = text.lower()
    hits = sum(1 for term in terms if term in lower)
    return hits / len(terms)


def _best_lines(text: str, terms: list[str]) -> list[tuple[float, str]]:
    if not text or not terms:
        return []
    ranked: list[tuple[float, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or re.match(r"^#+\s", line):
            continue
        score = _keyword_score(line, terms)
        if score > 0:
            ranked.append((score, line))
    ranked.sort(key=lambda pair: (-pair[0], -len(pair[1])))
    return ranked


def compose_retrieve_only_answer(question: str, documents: list[str]) -> str:
    terms = _question_terms(question)
    for doc in documents:
        doc_lines = _best_lines(doc or "", terms)
        if doc_lines:
            line = doc_lines[0][1]
            line = re.sub(r"^[-*]\s+", "", line)
            line = line.replace("**", "")
            return line.strip()

    if documents and documents[0]:
        snippet = documents[0].strip()
        if len(snippet) > 400:
            snippet = snippet[:400].rsplit(" ", 1)[0] + "…"
        return snippet

    return "No matching content found in the indexed documents for this question."


def offline_rag_result() -> RagResult:
    """Static mock payload (RAG_OFFLINE_MODE=mock)."""
    return RagResult(
        answer=OFFLINE_MOCK_ANSWER,
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


def _distance_to_score(dist: float | None) -> float:
    if dist is None:
        return 0.0
    return round(1.0 / (1.0 + float(dist)), 4)


def _sources_from_hits(
    documents: list[str],
    metadatas: list[dict],
    distances: list[float | None],
) -> list[SourceCitation]:
    sources: list[SourceCitation] = []
    for doc, meta, dist in zip(documents, metadatas, distances, strict=True):
        snippet = (doc or "")[:240]
        sources.append(
            SourceCitation(
                source=meta.get("source", ""),
                chunk_id=meta.get("chunk_id", ""),
                doc_id=meta.get("doc_id", ""),
                score=_distance_to_score(dist),
                snippet=snippet,
            )
        )
    return sources


def _offline_keyword_retrieve(
    question: str,
    collection,
    settings: Settings,
) -> tuple[list[str], list[dict], list[float | None]]:
    payload = collection.get(include=["documents", "metadatas"])
    documents = payload.get("documents") or []
    metadatas = payload.get("metadatas") or []
    terms = _question_terms(question)

    scored: list[tuple[float, str, dict]] = []
    for doc, meta in zip(documents, metadatas, strict=True):
        score = _keyword_score(doc or "", terms)
        scored.append((score, doc or "", meta))

    scored.sort(key=lambda row: (-row[0], row[2].get("source", "")))
    top = scored[: settings.top_k]
    if not top:
        return [], [], []

    docs = [row[1] for row in top]
    metas = [row[2] for row in top]
    # Higher score → lower pseudo-distance for API consumers.
    dists: list[float | None] = [None if row[0] <= 0 else 1.0 - row[0] for row in top]
    return docs, metas, dists


def _retrieve_offline(
    question: str,
    settings: Settings,
) -> tuple[list[str], list[dict], list[float | None]]:
    collection = get_collection(settings)
    return _offline_keyword_retrieve(question, collection, settings)


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
        if s.rag_offline_mode == "mock":
            result = offline_rag_result()
            result.latency_ms = (time.perf_counter() - started) * 1000
            return result

        collection = get_collection(s)
        if collection.count() == 0:
            raise RuntimeError("index is empty; run ingest first")

        documents, metadatas, distances = _retrieve_offline(question, s)
        sources = _sources_from_hits(documents, metadatas, distances)
        text = compose_retrieve_only_answer(question, documents)
        latency_ms = (time.perf_counter() - started) * 1000
        return RagResult(
            answer=text,
            sources=sources,
            usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            latency_ms=round(latency_ms, 2),
        )

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

    sources = _sources_from_hits(documents, metadatas, distances)

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