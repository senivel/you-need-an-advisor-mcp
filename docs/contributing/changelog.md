# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
