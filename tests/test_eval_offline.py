import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_run_eval_offline_passes() -> None:
    env = os.environ.copy()
    env["RAG_OFFLINE"] = "1"
    result = subprocess.run(
        [sys.executable, "scripts/run_eval.py", "--offline"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "Pass rate: 5/5" in result.stdout


def test_eval_json_cases_reference_raw_files() -> None:
    data = json.loads((ROOT / "eval.json").read_text(encoding="utf-8"))
    raw_files = {p.name for p in (ROOT / "data" / "raw").glob("*.*")}
    for case in data["cases"]:
        src = case.get("expected_source")
        if src:
            assert src in raw_files