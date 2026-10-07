"""Run the assistant against known questions and check the answers.

Usage (calls the real API, costs a few cents):
    ANTHROPIC_API_KEY=... python evals/run_evals.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.assistant import AnthropicClient, CVAssistant  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.prepared import PreparedAnswers, detect_lang  # noqa: E402
from app.retrieval import Retriever, load_chunks  # noqa: E402


def main() -> int:
    s = get_settings()
    kb = ROOT / "knowledge"
    bot = CVAssistant(Retriever(load_chunks(kb)), (kb / "_summary.md").read_text(),
                      (kb / "_contact.md").read_text(), AnthropicClient(s.api_key), s.model,
                      s.max_output_tokens, s.max_history_messages)
    prepared = PreparedAnswers(kb / "answers.json")
    cases = json.loads((ROOT / "evals" / "cases.json").read_text())
    failures = 0
    for c in cases:
        # Always the model (the API would serve some questions from prepared answers), with
        # the same search hint the API gives it.
        hint = prepared.hint(c["q"], detect_lang(c["q"]))
        ans = bot.answer([{"role": "user", "content": c["q"]}], hint=hint)["answer"]
        ok = all(re.search(p, ans, re.I) for p in c.get("must_include", []))
        ok &= not any(re.search(re.escape(p), ans, re.I) for p in c.get("must_not_include", []))
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {c['q']}\n      {ans[:160]!r}\n")
    print(f"{len(cases) - failures}/{len(cases)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
