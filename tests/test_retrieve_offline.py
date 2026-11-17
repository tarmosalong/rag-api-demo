import pytest
from src.config import get_settings
from src.ingest import ingest_directory
from src.rag import answer


@pytest.fixture
def seeded_offline(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "project-overview.md").write_text(
        "# Overview\n\n- Project name: **rag-api-demo**\n",
        encoding="utf-8",
    )
    chroma = tmp_path / "chroma"
    cache = tmp_path / "embed_cache.sqlite"
    monkeypatch.setenv("RAW_DIR", str(raw))
    monkeypatch.setenv("CHROMA_PATH", str(chroma))
    monkeypatch.setenv("EMBED_CACHE_PATH", str(cache))
    monkeypatch.setenv("RAG_OFFLINE", "1")
    monkeypatch.setenv("RAG_OFFLINE_MODE", "retrieve")
    get_settings.cache_clear()
    ingest_directory(rebuild=True, use_offline_embeddings=True)
    yield
    get_settings.cache_clear()


def test_retrieve_offline_answer_from_corpus(seeded_offline) -> None:
    result = answer("What is the project name?")
    assert "rag-api-demo" in result.answer.lower()
    assert result.usage.total_tokens == 0
    assert result.sources
    assert result.sources[0].source == "project-overview.md"