from __future__ import annotations

import argparse
import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path

from src.chroma_store import get_chroma_client, get_collection
from src.chunking import chunk_text
from src.config import Settings, get_settings
from src.embed_cache import EmbedCache
from src.offline_embed import offline_embedding
from src.xai_client import embed_texts

logger = logging.getLogger(__name__)


def _doc_id_for_path(path: Path) -> str:
    return path.stem


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_document(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _embed_chunks(chunks: list[str], cache: EmbedCache, settings: Settings) -> list[list[float]]:
    out: list[list[float] | None] = [None] * len(chunks)
    missing_texts: list[str] = []
    missing_positions: list[int] = []

    for i, chunk in enumerate(chunks):
        cached = cache.get(_content_hash(chunk))
        if cached is not None:
            out[i] = cached
        else:
            missing_texts.append(chunk)
            missing_positions.append(i)

    for start in range(0, len(missing_texts), settings.embed_batch_size):
        batch = missing_texts[start : start + settings.embed_batch_size]
        vectors = embed_texts(batch, settings)
        for chunk, vector in zip(batch, vectors, strict=True):
            pos = missing_positions[start + batch.index(chunk)]
            out[pos] = vector
            cache.put(_content_hash(chunk), vector)

    return [v for v in out if v is not None]  # type: ignore[misc]


def ingest_file(
    path: Path,
    *,
    settings: Settings | None = None,
    rebuild_collection: bool = False,
    use_offline_embeddings: bool = False,
) -> int:
    s = settings or get_settings()
    if path.suffix.lower() not in {".txt", ".md"}:
        raise ValueError(f"unsupported file type: {path.suffix}")

    text = read_document(path)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    if rebuild_collection:
        client = get_chroma_client(s)
        try:
            client.delete_collection(s.collection_name)
        except Exception:
            pass

    collection = get_collection(s)
    cache = EmbedCache(s.embed_cache_path)
    doc_id = _doc_id_for_path(path)
    source = path.name

    missing_texts: list[str] = []
    missing_positions: list[int] = []
    embeddings: list[list[float] | None] = [None] * len(chunks)

    for i, chunk in enumerate(chunks):
        cached = cache.get(_content_hash(chunk))
        if cached is not None:
            embeddings[i] = cached
        else:
            missing_texts.append(chunk)
            missing_positions.append(i)

    if use_offline_embeddings:
        for pos in missing_positions:
            chunk = chunks[pos]
            vector = offline_embedding(chunk)
            embeddings[pos] = vector
            cache.put(_content_hash(chunk), vector)
    else:
        for batch_start in range(0, len(missing_texts), s.embed_batch_size):
            batch = missing_texts[batch_start : batch_start + s.embed_batch_size]
            batch_positions = missing_positions[batch_start : batch_start + len(batch)]
            vectors = embed_texts(batch, s)
            for chunk, vector, pos in zip(batch, vectors, batch_positions, strict=True):
                embeddings[pos] = vector
                cache.put(_content_hash(chunk), vector)

    final_embeddings = [e for e in embeddings if e is not None]
    assert len(final_embeddings) == len(chunks)

    ids: list[str] = []
    metadatas: list[dict[str, str]] = []
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}:{idx}"
        ids.append(chunk_id)
        metadatas.append({"source": source, "chunk_id": chunk_id, "doc_id": doc_id})

    existing = collection.get(where={"doc_id": doc_id}, include=[])
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    collection.upsert(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
        embeddings=final_embeddings,
    )
    cache.set_last_ingest_at(datetime.now(UTC).isoformat())
    cache.close()
    logger.info("ingested %s chunks=%s", source, len(chunks))
    return len(chunks)


def ingest_directory(
    raw_dir: Path | None = None,
    *,
    settings: Settings | None = None,
    rebuild: bool = False,
    use_offline_embeddings: bool = False,
) -> int:
    s = settings or get_settings()
    directory = raw_dir or s.raw_dir
    paths = sorted(directory.glob("*.md")) + sorted(directory.glob("*.txt"))
    total = 0
    for i, path in enumerate(paths):
        total += ingest_file(
            path,
            settings=s,
            rebuild_collection=rebuild and i == 0,
            use_offline_embeddings=use_offline_embeddings,
        )
    return total


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Ingest data/raw into Chroma")
    parser.add_argument("--rebuild", action="store_true", help="drop collection before full ingest")
    parser.add_argument("--file", type=Path, help="ingest single file only")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="hash-based fake embeddings (no xAI calls)",
    )
    args = parser.parse_args()

    if args.file:
        count = ingest_file(
            args.file,
            rebuild_collection=False,
            use_offline_embeddings=args.offline,
        )
    else:
        count = ingest_directory(rebuild=args.rebuild, use_offline_embeddings=args.offline)
    mode = "offline" if args.offline else "live"
    print(f"Ingested {count} chunks ({mode})")


if __name__ == "__main__":
    main()