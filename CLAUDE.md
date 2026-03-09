# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) server for YNAB (You Need A Budget) -- your AI-powered budget advisor (YNAA = "You Need an Advisor"). Python 3.13+, managed with uv.

## Commands

- `uv run pytest` — run all tests (sockets disabled by default via pytest-socket)
- `uv run pytest tests/test_foo.py::test_bar` — run a single test
- `uv run pytest -k "keyword"` — run tests matching keyword
- `uv run ruff check .` — lint
- `uv run ruff check --fix .` — lint with auto-fix
- `uv run ruff format .` — format
- `uv sync` — install/sync dependencies

## Code Style

- Ruff handles both linting and formatting (not separate tools)
- Nearly all ruff rules enabled (`select = ["ALL"]`) with specific ignores — check `pyproject.toml [tool.ruff.lint]` for the full ignore list
- Google-style docstrings (`convention = "google"`)
- `ANN` (annotations) disabled project-wide — pyright strict owns type checking
- Tests additionally exempt from `D102`, `DOC201`, `PLR2004`, `PLR6301`, `RUF069`
- Pre-commit runs: ruff lint+format, prettier (JSON/YAML/MD), pyright type check, and standard hooks (large files, trailing whitespace, merge conflict, TOML/JSON validity). A local hook blocks `.planning/` files from commits.

## Tool Preferences

- Prefer the Context7 MCP (`resolve-library-id` → `query-docs`) over web search when looking up library or framework documentation. Fall back to web search only if Context7 lacks coverage for the library in question.

## Testing Conventions

- **pytest-mock over unittest.mock** — use the `mocker` fixture instead of `from unittest.mock import patch/MagicMock/AsyncMock`. pytest-mock auto-cleans and is more pytest-idiomatic.
- **freezegun for wall-clock time** — use `@freeze_time` for tests involving `datetime.now()`, `date.today()`, or `time.time()`. Not applicable to `time.monotonic()` (use `mocker.patch` for monotonic).
- **Hypothesis for property-based tests** — use `@given` with strategies for functions with well-defined input/output contracts (converters, validators, parsers). Complements example-based tests, doesn't replace them.

## Environment

- `YNAB_PAT` — required. YNAB Personal Access Token, validated on server startup.
- Entry point: `ynaa-mcp` CLI (`src/ynaa_mcp/__main__.py:main`)

## Project Structure

- `src/ynaa_mcp/` — main package (src layout)
  - `tools/` — one module per domain (accounts, transactions, categories, etc.)
  - `templates/` — prompt/workflow/analysis templates (loaded via `importlib.resources`)
  - `client.py` — `YNABClient` (rate limiting, envelope unwrapping, milliunit conversion, delta caching)
  - `converters.py` — milliunit/dollar conversion, formatting helpers
  - `cache.py` — `CacheStore` with cross-invalidation rules
- `tests/` — mirrors `src/` structure; `conftest.py` has shared fixtures
- `pyproject.toml` — all tool config (ruff, pytest, pyright, coverage) lives here

## Architecture

- `app.py` creates `AppContext` (client + cache) via `lifespan()` — tools access it with `app = cast("AppContext", ctx.lifespan_context)`
- `server.py` imports tool modules for side effects only (decorator self-registration) — these imports are one-way; tool modules import from `app`, never the reverse
- All API calls go through `YNABClient` which handles rate limiting, envelope unwrapping, milliunit conversion, and delta caching transparently

## Adding New Tools

- Follow the consolidated action pattern: one `@mcp.tool()` per domain with `action: Literal["list", "get", "create", ...]` dispatch
- Always call `resolve_budget(app.client, budget_id_or_name, cache=app.cache)` for budget-aware tools
- Return structured plain text with indentation, not JSON — use `format_dollars()` for money display
- Import and register in `server.py` via side-effect import

## Milliunit Handling

- YNAB API uses milliunits (1000 = $1.00) — `YNABClient` auto-converts known fields on read via `MILLIUNIT_FIELDS`
- For write operations, use `dollars_to_milliunits()` from `converters.py` (uses `Decimal` internally to avoid float precision issues)
- Display money with `format_dollars()` — never format manually

## Output Formatting

- All tools return structured plain text, not JSON
- 2-space indentation for hierarchy
- Counts in headers (e.g., "5 categories found:")
- Status indicators: `[C]`/`[U]`/`[R]` for cleared/uncleared/reconciled

## Cache Cross-Invalidation

- Mutating transactions invalidates accounts and categories caches
- Mutating categories invalidates months cache
- New mutation tools must respect these rules in `cache.py`

## Template Patterns

- Prompt/workflow templates live in `src/ynaa_mcp/templates/`
- Loaded via `importlib.resources` at module level
- Tool references in templates are validated by `tests/test_template_refs.py` — action values must match tool `Literal` types

## Async Test Marker

- Add `@pytest.mark.anyio` to all async test functions (not `@pytest.mark.asyncio`)
