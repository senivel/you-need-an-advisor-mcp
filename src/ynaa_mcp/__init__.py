"""YNAB MCP server -- Model Context Protocol server for You Need A Budget."""

__version__ = "1.1.1"  # x-release-please-version

from ynaa_mcp.app import AppContext, mcp
from ynaa_mcp.budget_resolver import resolve_budget
from ynaa_mcp.client import YNABClient
from ynaa_mcp.converters import dollars_to_milliunits, milliunits_to_dollars
from ynaa_mcp.errors import YNABAPIError, format_error
from ynaa_mcp.rate_limiter import RateLimiter


__all__ = [
    "AppContext",
    "RateLimiter",
    "YNABAPIError",
    "YNABClient",
    "__version__",
    "dollars_to_milliunits",
    "format_error",
    "mcp",
    "milliunits_to_dollars",
    "resolve_budget",
]
