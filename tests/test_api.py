import pytest
from fastapi.testclient import TestClient
from src.chroma_store import get_collection
from src.config import get_settings
from src.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    chroma = tmp_path / "chroma"
    cache = tmp_path / "embed_cache.sqlite"
    monkeypatch.setenv("CHROMA_PATH", str(chroma))
    monkeypatch.setenv("EMBED_CACHE_PATH", str(cache))
    monkeypatch.setenv("RAG_OFFLINE", "1")
    monkeypatch.setenv("XAI_API_KEY", "")
    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


def _seed_index() -> None:
    collection = get_collection()
    collection.upsert(
        ids=["demo-handbook:0"],
        documents=["Demo corpus for offline tests."],
        metadatas=[
            {
                "source": "demo-handbook.txt",
                "chunk_id": "demo-handbook:0",
                "doc_id": "demo-handbook",
            }
        ],
        embeddings=[[0.01] * 32],
    )


def test_health_reports_index_not_ready(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["index_ready"] is False


def test_ask_returns_503_when_index_empty(client: TestClient) -> None:
    response = client.post("/v1/ask", json={"question": "What is the project name?"})
    assert response.status_code == 503


def test_ask_offline_contract_when_index_ready(client: TestClient) -> None:
    _seed_index()
    response = client.post("/v1/ask", json={"question": "What is the project name?"})
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert body["usage"]["total_tokens"] == 0
    assert len(body["sources"]) >= 1
    assert "request_id" in body
    assert response.headers.get("X-Request-Id")