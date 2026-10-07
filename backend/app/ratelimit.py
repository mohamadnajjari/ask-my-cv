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
