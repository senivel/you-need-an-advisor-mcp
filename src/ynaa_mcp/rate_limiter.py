"""Sliding window rate limiter for YNAB API requests.

YNAB enforces a hard limit of 200 requests per hour. This rate limiter
proactively denies requests at 190/hr (95% of the limit) to prevent
hitting the hard limit and receiving 429 responses. Uses a deque of
``time.monotonic()`` timestamps in a 1-hour sliding window.
"""

import time
from collections import deque


MAX_REQUESTS: int = 200
"""YNAB hard rate limit (requests per hour)."""

WINDOW_SECONDS: float = 3600.0
"""Sliding window duration in seconds (1 hour)."""

DENY_THRESHOLD: int = 190
"""Proactive throttle threshold (95% of hard limit)."""


class RateLimiter:
    """Sliding window rate limiter that tracks request timestamps.

    Tracks ``time.monotonic()`` timestamps in a deque and prunes entries
    older than :data:`WINDOW_SECONDS`. Denies new requests once the
    count reaches :data:`DENY_THRESHOLD`.

    Attributes:
        _timestamps: Deque of monotonic timestamps for requests in the window.
    """

    def __init__(self) -> None:
        """Initialize the rate limiter with an empty timestamp deque."""
        self._timestamps: deque[float] = deque()

    def _prune(self) -> None:
        """Remove timestamps older than the sliding window.

        Pops from the left (oldest entries) until all remaining
        timestamps are within ``WINDOW_SECONDS`` of the current time.
        """
        cutoff = time.monotonic() - WINDOW_SECONDS
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def check(self) -> tuple[bool, int, float | None]:
        """Check whether a new request is allowed.

        Prunes expired timestamps, then checks the count against
        :data:`DENY_THRESHOLD`.

        Returns:
            A 3-tuple of:
                - ``allowed``: True if a request can proceed.
                - ``current_count``: Number of requests in the window.
                - ``retry_after``: Seconds until the oldest request
                  expires from the window (None if allowed).
        """
        self._prune()
        current_count = len(self._timestamps)

        if current_count >= DENY_THRESHOLD:
            # Oldest timestamp determines when the window frees a slot
            oldest = self._timestamps[0]
            retry_after = (oldest + WINDOW_SECONDS) - time.monotonic()
            return False, current_count, max(retry_after, 0.0)

        return True, current_count, None

    def record(self) -> None:
        """Record a request timestamp in the sliding window."""
        self._timestamps.append(time.monotonic())
