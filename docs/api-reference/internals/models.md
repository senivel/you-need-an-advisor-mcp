# Models

Pydantic models and TypedDicts for YNAB API response shapes. Base models use `extra="ignore"` so additional fields returned by the YNAB API do not cause validation errors. TypedDicts provide lightweight structural types for raw API response dicts where key-access patterns need type safety.

---

<!-- prettier-ignore -->
::: ynab_mcp.models
    options:
      show_root_heading: true
      show_source: true
      members: true
      filters: ["!^_"]
