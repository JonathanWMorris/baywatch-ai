from __future__ import annotations

import threading
import time


class TTLValue:
    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self.value = None
        self.expires = 0.0
        self.lock = threading.Lock()

    def get_or_load(self, loader):
        with self.lock:
            if self.value is not None and time.monotonic() < self.expires:
                return self.value
            self.value = loader()
            self.expires = time.monotonic() + self.ttl
            return self.value

