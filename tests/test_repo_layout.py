from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_expected_directories_exist() -> None:
    for name in ("src", "static", "docs", "data/raw", "tests", "scripts", ".github/workflows"):
        assert (ROOT / name).is_dir(), f"missing {name}"


def test_sample_corpus_committed() -> None:
    raw = ROOT / "data" / "raw"
    files = list(raw.glob("*.md")) + list(raw.glob("*.txt"))
    assert len(files) >= 2, "data/raw/ needs at least 2 sample documents"