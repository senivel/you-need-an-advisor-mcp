"""Budget tools: list budgets, get budget detail, get user info."""

from fastmcp import Context

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget


@mcp.tool
async def list_budgets(ctx: Context) -> str:
    """List all available YNAB budgets.

    Returns a count header followed by a structured list of budget
    names, IDs, and last modified dates.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        Structured text with count header and budget details,
        or "No budgets found." if none exist.
    """
    app: AppContext = ctx.lifespan_context
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


@mcp.tool
async def get_budget(
    ctx: Context,
    budget_id_or_name: str | None = None,
) -> str:
    """Get detailed information about a YNAB budget.

    Fetches budget details and settings (date format, currency format)
    in a single response. Uses budget resolution to find the budget
    by UUID or fuzzy name match.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.

    Returns:
        Structured text with budget name, months, date format, and
        currency format.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

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


@mcp.tool
async def get_user(ctx: Context) -> str:
    """Get the authenticated YNAB user's information.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        Structured text with the user ID.
    """
    app: AppContext = ctx.lifespan_context
    data = await app.client.get("/user")
    user = data["user"]
    return f"User ID: {user['id']}"
