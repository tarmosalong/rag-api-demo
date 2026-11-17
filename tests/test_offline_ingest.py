
import pytest
from src.chroma_store import index_ready, index_stats
from src.config import get_settings
from src.ingest import ingest_directory


@pytest.fixture
def offline_ingest_env(tmp_path, monkeypatch):
    chroma = tmp_path / "chroma"
    cache = tmp_path / "cache.sqlite"
    monkeypatch.setenv("CHROMA_PATH", str(chroma))
    monkeypatch.setenv("EMBED_CACHE_PATH", str(cache))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_offline_ingest_builds_index(offline_ingest_env) -> None:
    count = ingest_directory(rebuild=True, use_offline_embeddings=True)
    assert count > 0
    assert index_ready()
    docs, chunks = index_stats()
    assert docs >= 2
    assert chunks == count