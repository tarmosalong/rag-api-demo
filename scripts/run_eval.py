#!/usr/bin/env python3
"""Run eval.json cases in offline (contract) or live (quality) mode."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import get_settings
from src.rag import answer


def _load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("cases", [])


def _source_hit(sources: list, expected: str | None) -> bool:
    if not expected:
        return True
    return any(s.source == expected for s in sources)


def _run_case(case: dict, *, live: bool) -> tuple[bool, str]:
    question = case["question"]
    if live:
        get_settings.cache_clear()
        os.environ["RAG_OFFLINE"] = "0"
        get_settings.cache_clear()
        try:
            result = answer(question)
        except Exception as exc:
            return False, f"error: {exc}"
    else:
        os.environ["RAG_OFFLINE"] = "1"
        get_settings.cache_clear()
        result = answer(question)

    checks = case.get("offline_must_contain" if not live else "must_contain", [])
    for needle in checks:
        if needle.lower() not in result.answer.lower():
            return False, f"missing '{needle}' in answer"

    for forbidden in case.get("must_not_contain", []):
        if forbidden.lower() in result.answer.lower():
            return False, f"forbidden '{forbidden}' in answer"

    if live and case.get("expected_source"):
        if not _source_hit(result.sources, case["expected_source"]):
            names = [s.source for s in result.sources]
            return False, f"expected source {case['expected_source']}, got {names}"

    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--offline", action="store_true", help="contract eval (RAG_OFFLINE=1)")
    group.add_argument("--live", action="store_true", help="quality eval (xAI + indexed corpus)")
    parser.add_argument("--eval-file", type=Path, default=ROOT / "eval.json")
    args = parser.parse_args()

    cases = _load_cases(args.eval_file)
    passed = 0
    rows: list[tuple[str, str, str]] = []

    for case in cases:
        ok, detail = _run_case(case, live=args.live)
        passed += int(ok)
        rows.append((case.get("id", "?"), "PASS" if ok else "FAIL", detail))

    width = max(len(r[0]) for r in rows) if rows else 4
    for case_id, status, detail in rows:
        print(f"{case_id:<{width}}  {status}  {detail}")

    rate = (passed / len(cases) * 100) if cases else 0.0
    print(f"\nPass rate: {passed}/{len(cases)} ({rate:.0f}%)")
    if args.live and passed < len(cases):
        print("Live eval requires make ingest and a valid XAI_API_KEY in .env", file=sys.stderr)

    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())