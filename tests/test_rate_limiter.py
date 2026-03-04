"""Tests for the sliding window rate limiter."""

from ynab_mcp.rate_limiter import RateLimiter


class TestRateLimiterCheck:
    """Tests for RateLimiter.check() behavior."""

    def test_fresh_limiter_allows_requests(self):
        """Fresh limiter with no recorded requests allows requests."""
        limiter = RateLimiter()
        allowed, count, retry_after = limiter.check()

        assert allowed is True
        assert count == 0
        assert retry_after is None

    def test_denies_at_threshold(self, mocker):
        """After 190 recorded requests, check returns denied."""
        limiter = RateLimiter()
        base_time = 1000.0

        mock_time = mocker.patch("ynab_mcp.rate_limiter.time")
        mock_time.monotonic.return_value = base_time
        for _ in range(190):
            limiter.record()

        mock_time.monotonic.return_value = base_time + 1.0
        allowed, count, retry_after = limiter.check()

        assert allowed is False
        assert count == 190
        assert retry_after is not None
        assert retry_after > 0

    def test_allows_at_189_requests(self, mocker):
        """At 189 requests, still allowed (threshold is 190)."""
        limiter = RateLimiter()
        base_time = 1000.0

        mock_time = mocker.patch("ynab_mcp.rate_limiter.time")
        mock_time.monotonic.return_value = base_time
        for _ in range(189):
            limiter.record()

        mock_time.monotonic.return_value = base_time + 1.0
        allowed, count, retry_after = limiter.check()

        assert allowed is True
        assert count == 189
        assert retry_after is None

    def test_denied_includes_retry_after(self, mocker):
        """Denied response includes retry_after_seconds > 0."""
        limiter = RateLimiter()
        base_time = 1000.0

        mock_time = mocker.patch("ynab_mcp.rate_limiter.time")
        mock_time.monotonic.return_value = base_time
        for _ in range(190):
            limiter.record()

        # Check 10 seconds after the first request
        mock_time.monotonic.return_value = base_time + 10.0
        allowed, _count, retry_after = limiter.check()

        assert allowed is False
        assert retry_after is not None
        # Oldest request was at base_time, window is 3600s,
        # so retry_after should be ~3590s
        assert 3589.0 <= retry_after <= 3591.0

    def test_allows_after_window_expires(self, mocker):
        """After window expires, requests are allowed again."""
        limiter = RateLimiter()
        base_time = 1000.0

        mock_time = mocker.patch("ynab_mcp.rate_limiter.time")
        mock_time.monotonic.return_value = base_time
        for _ in range(190):
            limiter.record()

        # Advance time past the window
        mock_time.monotonic.return_value = base_time + 3601.0
        allowed, count, retry_after = limiter.check()

        assert allowed is True
        assert count == 0
        assert retry_after is None

    def test_old_requests_pruned(self, mocker):
        """Requests older than WINDOW_SECONDS are pruned."""
        limiter = RateLimiter()
        base_time = 1000.0

        mock_time = mocker.patch("ynab_mcp.rate_limiter.time")
        # Record 50 requests at base_time
        mock_time.monotonic.return_value = base_time
        for _ in range(50):
            limiter.record()

        # Record 10 more at base_time + 3500
        mock_time.monotonic.return_value = base_time + 3500.0
        for _ in range(10):
            limiter.record()

        # Check at base_time + 3601 -- first 50 should be pruned
        mock_time.monotonic.return_value = base_time + 3601.0
        allowed, count, retry_after = limiter.check()

        assert allowed is True
        assert count == 10
        assert retry_after is None


class TestRateLimiterRecord:
    """Tests for RateLimiter.record() behavior."""

    def test_record_adds_timestamp(self, mocker):
        """record() adds a timestamp to the tracking deque."""
        limiter = RateLimiter()

        mock_time = mocker.patch("ynab_mcp.rate_limiter.time")
        mock_time.monotonic.return_value = 42.0
        limiter.record()

        mock_time.monotonic.return_value = 43.0
        _, count, _ = limiter.check()

        assert count == 1


class TestRateLimiterCurrentCount:
    """Tests for current_count accuracy."""

    def test_current_count_reflects_window(self, mocker):
        """current_count reflects actual number of requests in window."""
        limiter = RateLimiter()
        base_time = 1000.0

        mock_time = mocker.patch("ynab_mcp.rate_limiter.time")
        mock_time.monotonic.return_value = base_time
        for _ in range(25):
            limiter.record()

        mock_time.monotonic.return_value = base_time + 1.0
        _, count, _ = limiter.check()

        assert count == 25
