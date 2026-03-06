# Architecture

YNAB MCP is built as an async MCP server using [FastMCP](https://github.com/jlowin/fastmcp), with a modular architecture that separates concerns into focused components.

## System Overview

```
Claude (AI Assistant)
    |
    v
FastMCP Server (server.py)
    |  - Wires tool, prompt, and resource modules
    |  - Manages lifespan (startup/shutdown)
    |
    v
Tool Modules (ynaa_mcp.tools.*)
    |  - budgets, accounts, categories, transactions
    |  - payees, months, scheduled, cache
    |  - Each module registers tools via @mcp.tool()
    |
    v
YNAB Client (client.py)
    |  - Single async httpx client instance
    |  - Rate limit checking before each request
    |  - Milliunit-to-dollar conversion on responses
    |  - YNAB error parsing
    |
    +---> Rate Limiter (rate_limiter.py)
    |       - Sliding window (200 req/hr)
    |       - Proactive throttling at 190 req/hr
    |
    +---> Converters (converters.py)
    |       - milliunits <-> dollars
    |       - Dollar formatting ($1,234.56)
    |       - Month normalization
    |
    +---> Cache Store (cache.py)
    |       - Delta caching with server_knowledge
    |       - TTL cache for budget list
    |
    v
YNAB API (api.ynab.com/v1)

Budget Resolver (budget_resolver.py)
    - Called by tools before API requests
    - Auto-selects single budget
    - Fuzzy name matching for multiple budgets
```

## Design Principles

**Lifespan-managed resources.** The httpx `AsyncClient` is created once during server startup and shared across all tool calls. No per-request client creation, no connection leaks.

**Modular tool registration.** Tool functions live in domain-specific modules under `ynaa_mcp.tools.*` (e.g., `tools/budgets.py`, `tools/transactions.py`). Each module imports the shared `mcp` instance from `app.py` and registers its tools via `@mcp.tool()`. The `server.py` file is a thin wiring layer that imports all modules.

**Boundary conversion.** YNAB uses milliunits internally (1 dollar = 1,000 milliunits). Conversion happens at the client layer so tools always work with human-readable dollar amounts.

**Proactive rate limiting.** Rather than waiting for 429 responses, the rate limiter denies requests at 95% capacity with a clear retry message.

**Automatic budget resolution.** Most YNAB users have a single budget. The resolver auto-selects it, eliminating unnecessary prompts while still supporting multi-budget setups via fuzzy name matching.

## YNAB Client

The `YNABClient` is the single point of contact with the YNAB API. All HTTP requests flow through this class, which handles rate limiting, error parsing, data envelope unwrapping, and milliunit conversion.

**Injected httpx client.** `YNABClient` does not create its own HTTP client. Instead, it receives a pre-configured `httpx.AsyncClient` during server lifespan startup. This means:

- One client instance for the entire server lifetime
- Base URL and Bearer auth configured once
- Automatic connection cleanup on shutdown
- Easy to mock in tests (inject a fake client)

**Request pipeline.** Every API call follows the same pipeline:

1. **Rate limit check** -- ask the `RateLimiter` if a request is allowed
2. **Send request** -- `httpx.AsyncClient.request(method, path)`
3. **Record timestamp** -- tell the `RateLimiter` a request was made
4. **Error handling** -- parse YNAB error responses into `YNABAPIError`
5. **Envelope unwrapping** -- extract the `data` key from the JSON response
6. **Milliunit conversion** -- recursively convert milliunit fields to dollars

**Milliunit field detection.** The client maintains a `MILLIUNIT_FIELDS` frozenset of known field names (like `balance`, `budgeted`, `activity`) plus suffix matching (`_balance`, `_amount`) for forward compatibility with new YNAB API fields.

## Rate Limiter

YNAB enforces a hard limit of **200 requests per hour**. The rate limiter proactively throttles requests to prevent hitting this limit and receiving 429 responses.

The rate limiter uses a **sliding window** algorithm:

- A `deque` stores `time.monotonic()` timestamps for each request
- Before each request, timestamps older than 1 hour are pruned
- If the count reaches **190 requests** (95% of the 200 limit), new requests are denied
- Denied requests receive a clear message with a retry-after time in seconds

The proactive threshold of 190 leaves a 10-request buffer for timing edge cases and in-flight requests. Using `time.monotonic()` (instead of `time.time()`) makes the window immune to system clock adjustments.

## Converters

YNAB stores all monetary amounts as **milliunits** -- 1 dollar equals 1,000 milliunits. The converters module handles translation between YNAB's internal format and human-readable dollar amounts.

Conversion happens at the **boundary** -- the `YNABClient` layer:

- **Inbound (API responses):** The client recursively walks response data and converts milliunit fields to dollar floats before any tool sees the data
- **Outbound (API requests):** Tools call `dollars_to_milliunits()` when sending write requests (creating accounts, setting budgets)

All intermediate arithmetic uses `decimal.Decimal` to avoid IEEE 754 floating-point drift.

## Budget Resolver

Every tool that operates on a budget calls `resolve_budget()` before making API requests. Resolution follows three paths:

1. **No identifier provided:** If you have exactly one budget, it's selected automatically. If you have multiple budgets, the tool returns an error listing available budgets.
2. **UUID provided:** Exact match against known budget IDs.
3. **Name provided:** Fuzzy matching using `difflib.SequenceMatcher` with a 60% similarity threshold, handling typos and partial names.
