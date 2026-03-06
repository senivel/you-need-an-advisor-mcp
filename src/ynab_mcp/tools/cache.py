"""Cache management tool: clear cached YNAB data."""

from typing import cast

from fastmcp import Context

from ynab_mcp.app import AppContext, mcp


@mcp.tool
def clear_cache(
    ctx: Context,
    budget_id: str | None = None,
) -> str:
    """Clear cached YNAB data to force fresh API requests.

    Use this if you've made changes in the YNAB app or web interface
    and want to ensure the latest data is fetched.

    Args:
        ctx: MCP context.
        budget_id: Optional budget ID to clear cache for.
            If not provided, clears all caches.

    Returns:
        Confirmation message.
    """
    app = cast("AppContext", ctx.lifespan_context)
    if budget_id:
        app.cache.invalidate_budget(budget_id)
        return f"Cache cleared for budget {budget_id}."
    app.cache.clear()
    return "All caches cleared."
