# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) server for YNAB (You Need A Budget). Python 3.13+, managed with uv.

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
- Tests are exempt from annotation (`ANN`) and `PLR6301` rules
- Pre-commit runs ruff lint+format and prettier (for JSON/YAML/MD) on commit

## Tool Preferences

- Prefer the Context7 MCP (`resolve-library-id` → `query-docs`) over web search when looking up library or framework documentation. Fall back to web search only if Context7 lacks coverage for the library in question.

## Project Structure

- `src/ynab_mcp/` — main package (src layout)
- `pyproject.toml` — all tool config (ruff, pytest, coverage) lives here
