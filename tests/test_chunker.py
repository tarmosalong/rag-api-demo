from src.chunking import chunk_text


def test_chunk_text_empty() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_short_passthrough() -> None:
    text = "Lühike tekst."
    assert chunk_text(text) == [text]


def test_chunk_text_overlap_produces_multiple() -> None:
    paragraph = "Lause. " * 200
    chunks = chunk_text(paragraph, chunk_size=200, overlap=50)
    assert len(chunks) >= 2
    assert all(len(c) <= 200 for c in chunks)