"""Shared answer cache: a question asked before (same language, same content words) is answered
from the stored answer, without a model call (0 tokens).

Only single questions are cached (a follow-up depends on its conversation). The key is the
language plus the question's content words, sorted, so word order, punctuation and case don't
matter. Entries expire after `ttl_days`; at most `max_entries` are kept (the oldest go first).
Saved to DATA_DIR like the budget, so a restart keeps them. `version` is a fingerprint of the
knowledge files: after any CV change, answers stored for the old version are never served again.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from threading import Lock
from typing import Any

from .retrieval import tokenize


class AnswerCache:
    def __init__(self, path: Path | None, ttl_days: int = 30, max_entries: int = 500,
                 clock=time.time, version: str = "") -> None:
        self.path, self.ttl, self.max = path, ttl_days * 86_400, max_entries
        self.clock = clock
        self.version = version
        self.lock = Lock()
        self.entries: dict[str, dict[str, Any]] = {}
        if path is not None and path.is_file():
            try:
                self.entries = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                self.entries = {}
        # Answers from an older CV are dropped (and gone from the file with the next save).
        self.entries = {k: v for k, v in self.entries.items() if k.startswith(f"{version}:")}

    def key(self, question: str, lang: str) -> str | None:
        words = sorted(set(tokenize(question)))
        return f"{self.version}:{lang}:{' '.join(words)}" if words else None

    def get(self, question: str, lang: str) -> dict[str, Any] | None:
        key = self.key(question, lang)
        with self.lock:
            entry = self.entries.get(key) if key else None
            if entry is None or self.clock() - entry["at"] > self.ttl:
                return None
            return entry

    def put(self, question: str, lang: str, answer: str, sources: list[str]) -> None:
        key = self.key(question, lang)
        if key is None or not answer:
            return
        with self.lock:
            self.entries[key] = {"answer": answer, "sources": sources, "at": self.clock()}
            if len(self.entries) > self.max:
                for old in sorted(self.entries, key=lambda k: self.entries[k]["at"])[: -self.max]:
                    del self.entries[old]
            self._save()

    def _save(self) -> None:
        if self.path is None:
            return
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".cache-")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False)
        os.replace(tmp, self.path)
