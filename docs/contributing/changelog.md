# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Documentation site** -- Complete MkDocs Material site with YNAB brand colors, user guide, API reference, and contributing docs
- **Workflow guide prompts** -- 6 step-by-step workflow templates: budget setup, debt payoff, financial review, savings planning, overspending recovery, new month prep
- **Analysis prompts** -- 6 analysis templates: spending trends, budget health, savings progress, income vs. expenses, category deep dive, financial snapshot
- **Core prompts** -- 3 foundational prompts: budget overview, transaction search, category analysis
- **YNAB methodology resources** -- 5 knowledge guides embedded as MCP resources: Four Rules, overspending, credit card management, reconciliation, Age of Money
- **Template system** -- Markdown-based prompt templates loaded via `importlib.resources`

### Changed

- **Tool consolidation** -- Reduced from 30+ individual tools to 8 consolidated tools (`manage_budgets`, `manage_accounts`, `manage_categories`, `manage_transactions`, `manage_payees`, `manage_months`, `manage_scheduled_transactions`, `manage_cache`) using action-based dispatch
- **Modular architecture** -- Refactored monolithic `server.py` into domain-specific modules: `tools/`, `prompts.py`, `analysis.py`, `workflows.py`, `resources.py`, `knowledge.py`
- **Entry point** -- Added `ynaa-mcp` console script via pyproject.toml for `uvx you-need-an-advisor-mcp` usage

### Improved

- **TTL cache** -- Uses `time.monotonic()` for clock-immune expiration with keyword-only `cache` parameter
- **Rate limiter** -- Sliding window implementation with proactive throttling at 190/200 requests
- **Type safety** -- TypedDicts for API response shapes, Pydantic models for domain objects, `py.typed` marker
- **Error handling** -- Structured `YNABAPIError` with HTTP status codes and actionable messages

## [0.1.0] - 2026-03-04

### Added

- MCP server built with FastMCP
- YNAB API authentication via Personal Access Token (environment variable)
- Budget tools: list budgets, get budget details, get user info
- Account tools: list accounts, get account details, create accounts
- Category tools: list categories, get category details, manage categories and category groups
- Monthly budget tools: get and set category budgets by month
- Automatic budget resolution (single budget auto-selected, fuzzy name matching for multiple)
- Proactive rate limiting with sliding window (200 req/hr, throttles at 190)
- Milliunit-to-dollar conversion at the client boundary using `decimal.Decimal`
- Structured error handling with `YNABAPIError` and MCP `ToolError`
- Async httpx client with lifespan management (single instance, automatic cleanup)
- Comprehensive test suite with pytest-socket (no network access), pytest-mock, freezegun, and Hypothesis
