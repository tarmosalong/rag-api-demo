from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    chat_model: str = "grok-3-fast-latest"
    embed_model: str = "grok-embedding-small"
    chroma_path: str = "data/chroma"
    top_k: int = 5
    max_output_tokens: int = 512
    max_context_chars: int = 6000
    embed_batch_size: int = 32
    ingest_on_startup: bool = False
    rag_offline: bool = False

    @field_validator("rag_offline", mode="before")
    @classmethod
    def _coerce_rag_offline(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    embed_cache_path: str = "data/embed_cache.sqlite"
    raw_dir: Path = Path("data/raw")
    collection_name: str = "rag_docs"
    upload_max_bytes: int = 5 * 1024 * 1024

    @property
    def chroma_dir(self) -> Path:
        return Path(self.chroma_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()