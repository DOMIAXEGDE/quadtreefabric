from __future__ import annotations

import threading
import time
from typing import Callable, Tuple


class ExecutorSession:
    """Stateful wrapper around a stateless executor function."""

    def __init__(self, fn: Callable[[str, dict | None], Tuple[bool, str]]):
        self.fn = fn
        self.globals: dict = {}
        self._lock = threading.RLock()

    def exec(self, code: str) -> Tuple[bool, str, float]:
        start = time.perf_counter()
        with self._lock:
            ok, out = self.fn(code, self.globals)
        return ok, out, time.perf_counter() - start

