from __future__ import annotations

from collections import defaultdict, deque
import time


class RateLimiter:
    def __init__(self, user_limit: int, guild_limit: int, window_seconds: int = 60) -> None:
        self._user_limit = user_limit
        self._guild_limit = guild_limit
        self._window = window_seconds
        self._user_events: dict[int, deque[float]] = defaultdict(deque)
        self._guild_events: dict[int, deque[float]] = defaultdict(deque)

    def allow_user(self, user_id: int) -> bool:
        return self._allow(self._user_events[user_id], self._user_limit)

    def allow_guild(self, guild_id: int) -> bool:
        return self._allow(self._guild_events[guild_id], self._guild_limit)

    def _allow(self, window: deque[float], limit: int) -> bool:
        now = time.monotonic()
        while window and now - window[0] > self._window:
            window.popleft()
        if len(window) >= limit:
            return False
        window.append(now)
        return True
