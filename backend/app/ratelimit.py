"""In-memory sliding-window rate limiter plus a global daily cap.

Good enough for a single small instance. For several instances, move the
counters to Redis.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self, per_ip: int, window_s: int, daily_cap: int) -> None:
        self.per_ip, self.window, self.daily_cap = per_ip, window_s, daily_cap
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.day = time.strftime("%Y-%m-%d")
        self.day_count = 0
        self.lock = Lock()

    def check(self, key: str, now: float | None = None) -> str | None:
        """Return None if allowed, otherwise a reason string."""
        now = time.time() if now is None else now
        with self.lock:
            today = time.strftime("%Y-%m-%d", time.gmtime(now))
            if today != self.day:
                self.day, self.day_count = today, 0
            if self.day_count >= self.daily_cap:
                return "daily_cap"
            q = self.hits[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.per_ip:
                return "rate_limited"
            q.append(now)
            self.day_count += 1
            return None


class DailyQuota:
    """How many AI answers each visitor (and everyone together) may get per UTC day.

    Prepared and cached answers don't count: they cost nothing. When a quota is used up, the
    visitor gets prepared answers instead of an error, so overuse costs nothing either.
    """

    def __init__(self, per_key: int, total: int) -> None:
        self.per_key, self.total = per_key, total
        self.day = ""
        self.used: dict[str, int] = defaultdict(int)
        self.used_total = 0
        self.lock = Lock()

    def take(self, key: str, now: float | None = None) -> str | None:
        """Count one AI answer for `key`; None if allowed, otherwise the reason."""
        now = time.time() if now is None else now
        with self.lock:
            today = time.strftime("%Y-%m-%d", time.gmtime(now))
            if today != self.day:  # a new day: everyone starts again (and old keys are dropped)
                self.day, self.used, self.used_total = today, defaultdict(int), 0
            if self.used_total >= self.total:
                return "daily_ai_cap"
            if self.used[key] >= self.per_key:
                return "visitor_ai_quota"
            self.used[key] += 1
            self.used_total += 1
            return None
