from pathlib import Path

from src.runtime_bootstrap import prepare_runtime

prepare_runtime()

import chromadb
from chromadb.api.models.Collection import Collection

from src.config import Settings, get_settings


def get_chroma_client(settings: Settings | None = None) -> chromadb.PersistentClient:
    s = settings or get_settings()
    path = Path(s.chroma_path)
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def get_collection(settings: Settings | None = None) -> Collection:
    s = settings or get_settings()
    client = get_chroma_client(s)
    return client.get_or_create_collection(
        name=s.collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def index_stats(settings: Settings | None = None) -> tuple[int, int]:
    """Return (unique doc_id count, chunk count)."""
    collection = get_collection(settings)
    count = collection.count()
    if count == 0:
        return 0, 0
    result = collection.get(include=["metadatas"])
    metas = result.get("metadatas") or []
    doc_ids = {m.get("doc_id") for m in metas if m and m.get("doc_id")}
    return len(doc_ids), count


def index_ready(settings: Settings | None = None) -> bool:
    return get_collection(settings).count() > 0