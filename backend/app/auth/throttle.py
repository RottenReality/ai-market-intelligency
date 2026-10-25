from collections import defaultdict, deque


class LoginThrottle:
    """Sliding-window counter of failed logins per key (client IP). In-memory, single process."""

    def __init__(self, max_failures: int = 5, window_seconds: float = 900) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> deque[float]:
        failures = self._failures[key]
        while failures and now - failures[0] > self.window_seconds:
            failures.popleft()
        return failures

    def is_blocked(self, key: str, now: float) -> bool:
        return len(self._prune(key, now)) >= self.max_failures

    def record_failure(self, key: str, now: float) -> None:
        self._prune(key, now).append(now)

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)
