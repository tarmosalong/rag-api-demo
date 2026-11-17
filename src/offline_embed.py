"""Deterministic fake embeddings for local dev without xAI credits."""

import hashlib

OFFLINE_EMBED_DIM = 384


def offline_embedding(text: str, *, dims: int = OFFLINE_EMBED_DIM) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    out: list[float] = []
    i = 0
    while len(out) < dims:
        block = digest if i == 0 else hashlib.sha256(digest + bytes([i % 256])).digest()
        for b in block:
            out.append((b / 127.5) - 1.0)
            if len(out) >= dims:
                break
        i += 1
    return out