# YNAB Client

The `YNABClient` is the single point of contact with the YNAB API. All HTTP requests flow through this class, which handles rate limiting, error parsing, data envelope unwrapping, and milliunit conversion.

## Design Decisions

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

## API Reference

::: ynab_mcp.client.YNABClient
options:
show_root_heading: true
show_source: true
members_order: source

::: ynab_mcp.client.MILLIUNIT_FIELDS
options:
show_root_heading: true
show_source: true
