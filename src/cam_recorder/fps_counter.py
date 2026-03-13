import time


class FpsCounter:
    def __init__(self, window: float = 2.0):
        self._window = window
        self._timestamps: list[float] = []

    def tick(self):
        now = time.monotonic()
        self._timestamps.append(now)
        cutoff = now - self._window
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def fps(self) -> float:
        if len(self._timestamps) < 2:
            return 0.0
        span = self._timestamps[-1] - self._timestamps[0]
        if span <= 0:
            return 0.0
        return (len(self._timestamps) - 1) / span
