"""Budget tools: list budgets, get budget detail, get user info."""

from typing import Literal, cast

from fastmcp import Context

from ynaa_mcp.app import AppContext, mcp
from ynaa_mcp.budget_resolver import resolve_budget


async def _list_budgets(app: AppContext) -> str:
    """List all available YNAB budgets.

    Args:
        app: The application context with client and cache.

    Returns:
        Structured text with count header and budget details.
    """
    data = await app.client.get("/budgets")
    budgets = data["budgets"]

    if not budgets:
        return "No budgets found."

    lines = [f"{len(budgets)} budgets found:"]
    for b in budgets:
        lines.extend((
            f"- {b['name']}",
            f"  ID: {b['id']}",
            f"  Last modified: {b['last_modified_on']}",
        ))
    return "\n".join(lines)


async def _get_budget(
    app: AppContext,
    budget_id: str,
    info: str | None,
) -> str:
    """Get detailed information about a YNAB budget.

    Args:
        app: The application context with client and cache.
        budget_id: Resolved budget UUID.
        info: Optional info message from budget resolution.

    Returns:
        Structured text with budget details and settings.
    """
    data = await app.client.get(f"/budgets/{budget_id}")
    budget = data["budget"]

    settings_data = await app.client.get(f"/budgets/{budget_id}/settings")
    settings = settings_data["settings"]

    date_fmt = settings.get("date_format", {}).get("format", "N/A")
    currency = settings.get("currency_format", {}).get("iso_code", "N/A")

    lines = [
        f"Budget: {budget['name']}",
        f"  ID: {budget['id']}",
        f"  First month: {budget['first_month']}",
        f"  Last month: {budget['last_month']}",
        f"  Date format: {date_fmt}",
        f"  Currency: {currency}",
    ]
    result = "\n".join(lines)

    if info:
        result = f"{info}\n\n{result}"
    return result


async def _get_user(app: AppContext) -> str:
    """Get the authenticated YNAB user's information.

    Args:
        app: The application context with client and cache.

    Returns:
        Structured text with the user ID.
    """
    data = await app.client.get("/user")
    user = data["user"]
    return f"User ID: {user['id']}"


@mcp.tool
async def manage_budgets(
    ctx: Context,
    action: Literal["list", "get", "get_user"],
    budget_id_or_name: str | None = None,
) -> str:
    """Manage YNAB budgets: list all, get details, or get user info.

    Actions:
        list: List all budgets. No extra params needed.
        get: Get budget details. Uses budget_id_or_name.
        get_user: Get authenticated user info. No extra params needed.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        action: The operation to perform.
        budget_id_or_name: Budget UUID or name (get only). Auto-resolves
            if only one budget exists.

    Returns:
        Structured text with budget or user information.
    """
    app = cast("AppContext", ctx.lifespan_context)

    if action == "list":
        return await _list_budgets(app)

    if action == "get":
        budget_id, info = await resolve_budget(
            app.client, budget_id_or_name, cache=app.cache
        )
        return await _get_budget(app, budget_id, info)

    return await _get_user(app)
