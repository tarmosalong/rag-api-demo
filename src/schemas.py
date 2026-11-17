from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    source: str
    chunk_id: str
    doc_id: str
    score: float
    snippet: str


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class RagResult(BaseModel):
    answer: str
    sources: list[SourceCitation]
    usage: TokenUsage
    latency_ms: float


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
    usage: TokenUsage
    latency_ms: float
    request_id: str


class HealthResponse(BaseModel):
    status: str
    index_ready: bool
    version: str


class StatsResponse(BaseModel):
    document_count: int
    chunk_count: int
    last_ingest_at: str | None


class UploadResponse(BaseModel):
    doc_id: str
    chunk_count: int
    source: str