"""Context extraction helpers for MCP tool modules.

Provides convenience functions to extract typed dependencies from the
MCP context's lifespan_context, avoiding repetitive casting in every
tool function.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from fastmcp import Context

    from ynaa_mcp.app import AppContext
    from ynaa_mcp.cache import CacheStore
    from ynaa_mcp.client import YNABClient


def get_app(ctx: Context) -> AppContext:
    """Extract the full AppContext from the MCP context.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        The AppContext instance with client and cache.
    """
    return cast("AppContext", ctx.lifespan_context)


def get_client(ctx: Context) -> YNABClient:
    """Extract the YNAB API client from the MCP context.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        The authenticated YNABClient instance.
    """
    app = cast("AppContext", ctx.lifespan_context)
    return app.client


def get_cache(ctx: Context) -> CacheStore:
    """Extract the cache store from the MCP context.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        The CacheStore instance.
    """
    app = cast("AppContext", ctx.lifespan_context)
    return app.cache
