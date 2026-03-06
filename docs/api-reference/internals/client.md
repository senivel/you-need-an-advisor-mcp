# Client

The async HTTP client handles all communication with the YNAB API. Every request flows through `YNABClient`, which provides authentication, rate limit enforcement, error parsing, response unwrapping, and milliunit-to-dollar conversion.

## Key behaviors

- **Rate limiting:** Checks remaining quota before each request and raises `ToolError` if exhausted.
- **Authentication:** Bearer token injected via the httpx client at construction time.
- **Error parsing:** YNAB error responses are parsed into `YNABAPIError` with structured fields.
- **Data unwrapping:** Automatically extracts the `data` envelope from YNAB API responses.
- **Milliunit conversion:** Converts milliunit fields (amounts in thousandths) to dollar values in responses.
- **Delta caching:** Supports server knowledge-based delta requests for supported endpoints.

---

<!-- prettier-ignore -->
::: ynab_mcp.client
    options:
      show_root_heading: true
      show_source: true
      members: true
      filters: ["!^_"]
