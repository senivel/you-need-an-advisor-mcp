# Architecture

YNAB MCP is built as an async MCP server using [FastMCP](https://github.com/jlowin/fastmcp), with a modular architecture that separates concerns into focused components.

## System Overview

```
Claude (AI Assistant)
    |
    v
FastMCP Server (server.py)
    |  - Registers MCP tools
    |  - Manages lifespan (startup/shutdown)
    |  - Formats responses as structured text
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
    v
YNAB API (api.ynab.com/v1)

Budget Resolver (budget_resolver.py)
    - Called by tools before API requests
    - Auto-selects single budget
    - Fuzzy name matching for multiple budgets
```

## Design Principles

**Lifespan-managed resources.** The httpx `AsyncClient` is created once during server startup and shared across all tool calls. No per-request client creation, no connection leaks.

**Boundary conversion.** YNAB uses milliunits internally (1 dollar = 1,000 milliunits). Conversion happens at the client layer so tools always work with human-readable dollar amounts.

**Proactive rate limiting.** Rather than waiting for 429 responses, the rate limiter denies requests at 95% capacity with a clear retry message.

**Automatic budget resolution.** Most YNAB users have a single budget. The resolver auto-selects it, eliminating unnecessary prompts while still supporting multi-budget setups via fuzzy name matching.

## Internal Modules

| Module               | Purpose                                             | Detail Page                           |
| -------------------- | --------------------------------------------------- | ------------------------------------- |
| `client.py`          | Async HTTP client with rate limiting and conversion | [YNAB Client](client.md)              |
| `rate_limiter.py`    | Sliding window rate limiter (200 req/hr)            | [Rate Limiter](rate-limiter.md)       |
| `converters.py`      | Milliunit/dollar conversion and formatting          | [Converters](converters.md)           |
| `budget_resolver.py` | Budget auto-resolution and fuzzy matching           | [Budget Resolver](budget-resolver.md) |
