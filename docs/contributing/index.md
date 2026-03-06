# Contributing

Thanks for your interest in contributing to YNAB MCP! This guide covers everything you need to get started.

## Development setup

**1. Clone the repository:**

```bash
git clone https://github.com/senivel/ynab-mcp.git
cd ynab-mcp
```

**2. Install dependencies** (requires [uv](https://docs.astral.sh/uv/)):

```bash
uv sync --group dev --group docs
```

**3. Install pre-commit hooks:**

```bash
uv run pre-commit install
```

Pre-commit runs [Ruff](https://docs.astral.sh/ruff/) (lint + format) and [Prettier](https://prettier.io/) (JSON, YAML, Markdown) on every commit.

## Running tests

Tests use [pytest](https://docs.pytest.org/) with [pytest-socket](https://pypi.org/project/pytest-socket/) to disable network access by default -- no real YNAB API calls during testing.

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_client.py

# Run tests matching a keyword
uv run pytest -k "rate_limit"

# Run with verbose output
uv run pytest -v
```

### Testing conventions

- **pytest-mock** over `unittest.mock` -- use the `mocker` fixture for patching. It auto-cleans after each test and is more pytest-idiomatic.
- **freezegun** for wall-clock time -- use `@freeze_time` for tests involving `datetime.now()` or `date.today()`. Not applicable to `time.monotonic()` (use `mocker.patch` for monotonic).
- **Hypothesis** for property-based tests -- use `@given` with strategies for functions with well-defined input/output contracts (converters, validators, parsers). Complements example-based tests, doesn't replace them.

## Code style

[Ruff](https://docs.astral.sh/ruff/) handles both linting and formatting. The project uses an aggressive rule set:

```toml
[tool.ruff.lint]
select = ["ALL"]
```

With specific ignores listed in `pyproject.toml`. In practice this means:

- **Type annotations on everything** -- public functions, methods, parameters, return types
- **Google-style docstrings** on all public functions and classes
- **No magic numbers** -- use named constants or `http.HTTPStatus`

Run the linter manually:

```bash
# Check for issues
uv run ruff check .

# Auto-fix what's possible
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Project structure

```
src/ynab_mcp/
  app.py              # FastMCP instance, AppContext, lifespan
  server.py            # Module wiring (imports all tool/prompt/resource modules)
  client.py            # Async YNAB API client (httpx)
  models.py            # Pydantic models and TypedDicts for API responses
  errors.py            # YNABAPIError, error handling utilities
  budget_resolver.py   # Automatic budget ID resolution
  cache.py             # TTL cache with monotonic clock expiration
  rate_limiter.py      # Sliding window rate limiter (200 req/hr)
  converters.py        # Milliunit-to-dollar and data transformations
  knowledge.py         # YNAB methodology resource loader
  resources.py         # MCP resource definitions
  prompts.py           # Core MCP prompt definitions
  analysis.py          # Analysis prompt templates (6 prompts)
  workflows.py         # Workflow guide prompt templates (6 prompts)
  tools/
    budgets.py         # manage_budgets tool
    accounts.py        # manage_accounts tool
    categories.py      # manage_categories tool
    transactions.py    # manage_transactions tool
    payees.py          # manage_payees tool
    months.py          # manage_months tool
    scheduled.py       # manage_scheduled_transactions tool
    cache.py           # manage_cache tool
    _helpers.py        # Shared tool utilities
  methodology/         # YNAB methodology markdown guides
  templates/           # Prompt template markdown files
```

Each tool module registers a single consolidated tool (e.g., `manage_budgets`) that dispatches to private helper functions based on an `action` parameter.

## Documentation

Documentation is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and auto-generated API reference via [mkdocstrings](https://mkdocstrings.github.io/).

```bash
# Start local preview server (hot-reload)
uv run --group docs mkdocs serve

# Build static site
uv run --group docs mkdocs build --strict
```

The `docs/` directory mirrors the site navigation. Add new pages by creating a Markdown file and adding it to the `nav:` section in `mkdocs.yml`.

## Pull request process

1. **Fork and clone** the repository
2. **Create a branch** from `dev` (not `main`)
3. **Use conventional commits:**
   - `feat:` -- new feature
   - `fix:` -- bug fix
   - `docs:` -- documentation only
   - `test:` -- adding or updating tests
   - `chore:` -- maintenance, dependencies, tooling
   - `refactor:` -- code change that doesn't fix a bug or add a feature
4. **Ensure checks pass:**

   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```

5. **Open a PR** against `dev` with a clear description of what changed and why

## Questions?

Open an issue on [GitHub](https://github.com/senivel/ynab-mcp/issues) if you have questions or run into problems.
