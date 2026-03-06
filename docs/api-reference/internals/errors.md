# Errors

Error types for YNAB API errors and validation failures. Error messages differentiate between user errors (4xx) and server errors (5xx), with retry hints for transient failures like rate limits (429) and server issues.

---

<!-- prettier-ignore -->
::: ynab_mcp.errors
    options:
      show_root_heading: true
      show_source: true
      members: true
      filters: ["!^_"]
