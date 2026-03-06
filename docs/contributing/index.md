# Contributing

Thanks for your interest in contributing to YNAB MCP! This guide covers everything you need to get started.

## Development Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/senivel/ynab-mcp.git
   cd ynab-mcp
   ```

2. **Install dependencies** (requires [uv](https://docs.astral.sh/uv/)):

   ```bash
   uv sync --group dev --group docs
   ```

3. **Install pre-commit hooks:**

   ```bash
   uv run pre-commit install
   ```

   Pre-commit runs [Ruff](https://docs.astral.sh/ruff/) (lint + format) and [Prettier](https://prettier.io/) (JSON, YAML, Markdown) on every commit.

## Running Tests

Tests use [pytest](https://docs.pytest.org/) with [pytest-socket](https://pypi.org/project/pytest-socket/) to disable network access by default — no real YNAB API calls during testing.

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

### Testing Conventions

- **pytest-mock** over `unittest.mock` — use the `mocker` fixture for patching
- **freezegun** for wall-clock time — use `@freeze_time` for tests involving `datetime.now()` or `date.today()`
- **Hypothesis** for property-based tests — use `@given` with strategies for functions with well-defined input/output contracts (converters, validators, parsers)

## Code Style

[Ruff](https://docs.astral.sh/ruff/) handles both linting and formatting. The project uses an aggressive rule set:

```toml
[tool.ruff.lint]
select = ["ALL"]
```

With specific ignores listed in `pyproject.toml`. In practice, this means:

- **Type annotations on everything** (public functions, methods, parameters, return types)
- **Google-style docstrings** on all public functions and classes
- **No magic numbers** — use named constants or `http.HTTPStatus`

Run the linter manually:

```bash
# Check for issues
uv run ruff check .

# Auto-fix what's possible
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Documentation

Documentation is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and auto-generated API reference via [mkdocstrings](https://mkdocstrings.github.io/).

```bash
# Start local preview server (hot-reload)
uv run --group docs mkdocs serve

# Build static site
uv run --group docs mkdocs build --strict
```

The `docs/` directory mirrors the site navigation. Add new pages by creating a Markdown file and adding it to the `nav:` section in `mkdocs.yml`.

## Pull Request Process

1. **Create a branch** from `dev` (not `main`)
2. **Use conventional commits:**
   - `feat:` — new feature
   - `fix:` — bug fix
   - `docs:` — documentation only
   - `test:` — adding or updating tests
   - `chore:` — maintenance, dependencies, tooling
   - `refactor:` — code change that doesn't fix a bug or add a feature
3. **Ensure checks pass:**

   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```

4. **Open a PR** against `dev` with a clear description of what changed and why
