"""Money budget: what the assistant may spend per day and per month, from real token usage.

Every answer's actual usage (input and output tokens, as Anthropic reports them) is converted to
whole micro-dollars (millionths of a dollar): with prices in USD per million tokens, tokens x
price is exactly that, rounded up, so spending is never under-counted. When the day's or the
month's budget is used up, the assistant refuses until the next day or month (UTC).

The totals are saved to a small JSON file (DATA_DIR), written atomically, so a restart or a
redeploy can't reset them. Without DATA_DIR they live in memory only (tests, local runs).
The provider's own monthly spend limit (Anthropic console) stays the last line of defence.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import time
from pathlib import Path
from threading import Lock
from typing import Callable

MICRO = 1_000_000


class Budget:
    def __init__(self, path: Path | None, daily_usd: float, monthly_usd: float,
                 usd_per_mtok_in: float, usd_per_mtok_out: float,
                 clock: Callable[[], float] = time.time) -> None:
        self.path = path
        self.daily = math.floor(daily_usd * MICRO)
        self.monthly = math.floor(monthly_usd * MICRO)
        self.price_in, self.price_out = usd_per_mtok_in, usd_per_mtok_out
        self.clock = clock
        self.lock = Lock()
        self.state = {"day": "", "day_micro": 0, "day_answers": 0, "month": "", "month_micro": 0}
        if path is not None and path.is_file():
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
                self.state.update({k: saved[k] for k in self.state if k in saved})
            except (ValueError, OSError):
                pass  # unreadable: start counting again; the provider's limit still applies

    def check(self) -> str | None:
        """None if one more answer may be paid for now, else the reason."""
        with self.lock:
            self._roll()
            if self.state["month_micro"] >= self.monthly:
                return "monthly_budget"
            if self.state["day_micro"] >= self.daily:
                return "daily_budget"
            return None

    def add(self, input_tokens: int, output_tokens: int) -> dict[str, int | str]:
        """Count one answer; returns its cost and the new totals (for the usage log)."""
        cost = math.ceil(input_tokens * self.price_in + output_tokens * self.price_out)
        with self.lock:
            self._roll()
            self.state["day_micro"] += cost
            self.state["day_answers"] += 1
            self.state["month_micro"] += cost
            self._save()
            return {"cost_micro_usd": cost, **self.state}

    def _roll(self) -> None:
        now = time.gmtime(self.clock())
        day, month = time.strftime("%Y-%m-%d", now), time.strftime("%Y-%m", now)
        if self.state["month"] != month:
            self.state.update(month=month, month_micro=0)
        if self.state["day"] != day:
            self.state.update(day=day, day_micro=0, day_answers=0)

    def _save(self) -> None:
        if self.path is None:
            return
        # A new file, then an atomic rename: a crash never leaves half a file behind.
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".usage-")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.state, f)
        os.replace(tmp, self.path)
