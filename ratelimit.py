"""Token-bucket rate limiter — thread-safe, refill-on-read."""
from __future__ import annotations

import threading
import time


class TokenBucket:
    def __init__(self, qps: float, burst: int) -> None:
        self.qps = qps
        self.burst = burst
        self.tokens = float(burst)
        self.ts = time.time()
        self.lock = threading.Lock()

    def allow(self, n: int = 1) -> bool:
        with self.lock:
            now = time.time()
            self.tokens = min(self.burst, self.tokens + (now - self.ts) * self.qps)
            self.ts = now
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False
