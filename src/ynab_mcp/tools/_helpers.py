"""Context extraction helpers for MCP tool modules.

Provides convenience functions to extract typed dependencies from the
MCP context's lifespan_context, avoiding repetitive casting in every
tool function.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from fastmcp import Context

    from ynab_mcp.app import AppContext
    from ynab_mcp.cache import CacheStore
    from ynab_mcp.client import YNABClient


def get_client(ctx: Context) -> YNABClient:
    """Extract the YNAB API client from the MCP context.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        The authenticated YNABClient instance.
    """
    app: AppContext = ctx.lifespan_context
    return app.client


def get_cache(ctx: Context) -> CacheStore:
    """Extract the cache store from the MCP context.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        The CacheStore instance.
    """
    app: AppContext = ctx.lifespan_context
    return app.cache
