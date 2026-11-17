def chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Sliding-window chunks with overlap; prefer breaking at paragraph or sentence."""
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            break_at = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("? "))
            if break_at > chunk_size // 2:
                end = start + break_at + (1 if window[break_at : break_at + 1] in ".?" else 2)

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks