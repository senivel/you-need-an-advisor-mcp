# Rate Limiter

YNAB enforces a hard limit of **200 requests per hour**. The rate limiter proactively throttles requests to prevent hitting this limit and receiving 429 responses.

## How It Works

The rate limiter uses a **sliding window** algorithm:

- A `deque` stores `time.monotonic()` timestamps for each request
- Before each request, timestamps older than 1 hour are pruned
- If the count reaches **190 requests** (95% of the 200 limit), new requests are denied
- Denied requests receive a clear message with a retry-after time in seconds

### Why 190, Not 200?

The proactive threshold of 190 leaves a 10-request buffer. This accounts for:

- Timing edge cases where multiple requests are in-flight
- Slight clock differences between client-side tracking and YNAB's server-side counting
- A safety margin so users never see a raw 429 error from YNAB

### Why `time.monotonic()`?

Unlike `time.time()`, `monotonic()` is not affected by system clock adjustments (NTP sync, manual changes, daylight saving). This prevents the sliding window from breaking if the system clock jumps forward or backward.

## API Reference

::: ynab_mcp.rate_limiter
options:
show_root_heading: true
show_source: true
members_order: source
