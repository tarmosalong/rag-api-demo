import json
import sqlite3
from pathlib import Path


class EmbedCache:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                content_hash TEXT PRIMARY KEY,
                embedding_json TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, content_hash: str) -> list[float] | None:
        row = self._conn.execute(
            "SELECT embedding_json FROM embeddings WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def put(self, content_hash: str, embedding: list[float]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO embeddings (content_hash, embedding_json) VALUES (?, ?)",
            (content_hash, json.dumps(embedding)),
        )
        self._conn.commit()

    def set_last_ingest_at(self, iso_timestamp: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_ingest_at', ?)",
            (iso_timestamp,),
        )
        self._conn.commit()

    def get_last_ingest_at(self) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = 'last_ingest_at'",
        ).fetchone()
        return row[0] if row else None

    def close(self) -> None:
        self._conn.close()