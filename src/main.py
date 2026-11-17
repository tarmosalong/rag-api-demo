import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.chroma_store import index_ready, index_stats
from src.config import APP_VERSION, get_settings
from src.ingest import ingest_directory, ingest_file
from src.middleware import RequestIdMiddleware
from src.rag import answer, get_stats
from src.schemas import (
    AskResponse,
    HealthResponse,
    QuestionRequest,
    StatsResponse,
    UploadResponse,
)

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def _raw_corpus_file_count(settings) -> int:
    raw = settings.raw_dir
    if not raw.is_dir():
        return 0
    return len(list(raw.glob("*.md")) + list(raw.glob("*.txt")))


def _should_seed_offline_index(settings) -> bool:
    if not settings.rag_offline:
        return False
    if not index_ready(settings):
        return True
    indexed_docs, _ = index_stats(settings)
    return indexed_docs < _raw_corpus_file_count(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.rag_auto_seed_offline and _should_seed_offline_index(settings):
        raw_n = _raw_corpus_file_count(settings)
        logger.info("RAG_OFFLINE: building index from data/raw (%s files)", raw_n)
        ingest_directory(
            settings=settings,
            rebuild=True,
            use_offline_embeddings=True,
        )
    elif settings.ingest_on_startup and not index_ready(settings):
        logger.info("INGEST_ON_STARTUP: running ingest")
        ingest_directory(settings=settings, rebuild=False)
    yield


app = FastAPI(title="rag-api-demo", version=APP_VERSION, lifespan=lifespan)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        index_ready=index_ready(),
        version=APP_VERSION,
    )


@app.get("/v1/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    doc_count, chunk_count, last_ingest = get_stats()
    return StatsResponse(
        document_count=doc_count,
        chunk_count=chunk_count,
        last_ingest_at=last_ingest,
    )


@app.post("/v1/ask", response_model=AskResponse)
def ask_question(body: QuestionRequest, request: Request) -> AskResponse:
    settings = get_settings()
    if not index_ready(settings):
        raise HTTPException(
            status_code=503,
            detail="Index is not ready. Run ingest first (make ingest).",
        )

    try:
        result = answer(body.question, settings=settings)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AskResponse(
        answer=result.answer,
        sources=result.sources,
        usage=result.usage,
        latency_ms=result.latency_ms,
        request_id=_request_id(request),
    )


@app.post("/v1/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
) -> UploadResponse:
    settings = get_settings()
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Only .txt and .md supported")

    data = await file.read()
    if len(data) > settings.upload_max_bytes:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB upload limit")

    dest = settings.raw_dir / Path(file.filename).name
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)

    try:
        chunk_count = ingest_file(
            dest,
            settings=settings,
            use_offline_embeddings=settings.rag_offline,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}") from exc

    return UploadResponse(
        doc_id=dest.stem,
        chunk_count=chunk_count,
        source=dest.name,
    )


@app.get("/", include_in_schema=False)
def web_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")