# -*- coding: utf-8 -*-
"""Simple rate limiter"""
import time
from threading import Lock
from modules.config import RATE_LIMIT_RPM


class RateLimiter:
    def __init__(self, rpm: int = None):
        self.rpm = rpm or RATE_LIMIT_RPM
        self.min_interval = 60.0 / self.rpm if self.rpm > 0 else 0
        self.last = 0
        self._lock = Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last
            if elapsed < self.min_interval and self.min_interval > 0:
                time.sleep(self.min_interval - elapsed)
            self.last = time.monotonic()


_limiter = RateLimiter()


def rate_limit() -> None:
    _limiter.wait()
