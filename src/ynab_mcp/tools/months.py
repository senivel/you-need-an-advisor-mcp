"""Month tools: consolidated manage_months with action-parameter dispatch."""

from typing import Any, Literal, cast

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.converters import format_dollars, normalize_month


async def _list_months(app: AppContext, budget_id: str) -> str:
    """List all budget months, excluding deleted ones.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.

    Returns:
        Structured text with count header and month summaries,
        or "No months found." if none exist.
    """
    data = await app.client.get(f"/budgets/{budget_id}/months")
    all_months = data["months"]

    months = [m for m in all_months if not m["deleted"]]

    if not months:
        return "No months found."

    count = len(months)
    noun = "month" if count == 1 else "months"
    lines = [f"{count} {noun} found:"]
    for m in months:
        parts = [
            f"- {m['month']}",
            f"    Income: {format_dollars(m['income'])}",
            f"    Budgeted: {format_dollars(m['budgeted'])}",
            f"    Activity: {format_dollars(m['activity'])}",
            f"    To be budgeted: {format_dollars(m['to_be_budgeted'])}",
        ]
        if m.get("age_of_money") is not None:
            parts.append(f"    Age of money: {m['age_of_money']} days")
        lines.extend(parts)

    return "\n".join(lines)


async def _get_month(app: AppContext, budget_id: str, month: str) -> str:
    """Get detailed information about a specific budget month.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.
        month: Month as "YYYY-MM" or "YYYY-MM-DD".

    Returns:
        Structured text with month summary and grouped category detail.
    """
    normalized = normalize_month(month)
    data = await app.client.get(f"/budgets/{budget_id}/months/{normalized}")
    m = data["month"]

    lines = [
        f"Month: {m['month']}",
        f"  Income: {format_dollars(m['income'])}",
        f"  Budgeted: {format_dollars(m['budgeted'])}",
        f"  Activity: {format_dollars(m['activity'])}",
        f"  To be budgeted: {format_dollars(m['to_be_budgeted'])}",
    ]
    if m.get("age_of_money") is not None:
        lines.append(f"  Age of money: {m['age_of_money']} days")

    # Group categories by category_group_name
    categories = m.get("categories", [])
    groups: dict[str, list[dict[str, Any]]] = {}
    for cat in categories:
        group_name = cat.get("category_group_name") or cat.get(
            "category_group_id", "Uncategorized"
        )
        groups.setdefault(group_name, []).append(cat)

    for group_name, cats in groups.items():
        lines.append(f"\n{group_name} ({len(cats)} categories):")
        for cat in cats:
            budget_line = (
                f"    Budgeted: {format_dollars(cat['budgeted'])} | "
                f"Activity: {format_dollars(cat['activity'])} | "
                f"Balance: {format_dollars(cat['balance'])}"
            )
            lines.extend((
                f"  - {cat['name']}",
                budget_line,
            ))

    return "\n".join(lines)


async def _list_money_movements(
    app: AppContext,
    budget_id: str,
    month: str | None,
) -> str:
    """List money movements in a budget, optionally scoped to a month.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.
        month: If provided, scope to this month ("YYYY-MM" or "YYYY-MM-DD").

    Returns:
        Structured text with count header and movement lines,
        or "No money movements found." if none exist.
    """
    if month is not None:
        normalized = normalize_month(month)
        path = f"/budgets/{budget_id}/months/{normalized}/money_movements"
    else:
        path = f"/budgets/{budget_id}/money_movements"

    data = await app.client.get(path)
    movements = data["money_movements"]

    if not movements:
        return "No money movements found."

    count = len(movements)
    noun = "money movement" if count == 1 else "money movements"
    lines = [f"{count} {noun} found:"]
    for mv in movements:
        cat_name = mv["category_name"]
        group = mv.get("category_group_name")
        label = f"{cat_name} ({group})" if group else cat_name
        lines.extend((
            f"- {label}",
            f"    Allocation: {format_dollars(mv['allocation'])}",
            f"    Spent: {format_dollars(mv['spent'])}",
            f"    Income: {format_dollars(mv['income'])}",
        ))

    return "\n".join(lines)


async def _list_money_movement_groups(
    app: AppContext,
    budget_id: str,
    month: str | None,
) -> str:
    """List money movement groups in a budget, optionally scoped to a month.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.
        month: If provided, scope to this month ("YYYY-MM" or "YYYY-MM-DD").

    Returns:
        Structured text with count header and group lines,
        or "No money movement groups found." if none exist.
    """
    if month is not None:
        normalized = normalize_month(month)
        path = f"/budgets/{budget_id}/months/{normalized}/money_movement_groups"
    else:
        path = f"/budgets/{budget_id}/money_movement_groups"

    data = await app.client.get(path)
    groups = data["money_movement_groups"]

    if not groups:
        return "No money movement groups found."

    count = len(groups)
    noun = "money movement group" if count == 1 else "money movement groups"
    lines = [f"{count} {noun} found:"]
    for grp in groups:
        lines.extend((
            f"- {grp['category_group_name']}",
            f"    Allocation: {format_dollars(grp['allocation'])}",
            f"    Spent: {format_dollars(grp['spent'])}",
            f"    Income: {format_dollars(grp['income'])}",
        ))

    return "\n".join(lines)


@mcp.tool
async def manage_months(
    ctx: Context,
    action: Literal[
        "list", "get", "list_money_movements", "list_money_movement_groups"
    ],
    budget_id_or_name: str = "last-used",
    month: str | None = None,
) -> str:
    """Manage YNAB budget months: list, get detail, and view money movements.

    Dispatches to the appropriate action based on the ``action`` parameter.

    Actions:
        list: List all budget months with income, budgeted, activity,
            to-be-budgeted, and age of money. Params: budget_id_or_name.
        get: Get detailed month with category breakdowns grouped by
            category group. Params: budget_id_or_name, month (required).
        list_money_movements: List money movements (category-level).
            Params: budget_id_or_name, month (optional -- all if omitted).
        list_money_movement_groups: List money movement groups (group-level).
            Params: budget_id_or_name, month (optional -- all if omitted).

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        action: The operation to perform.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        month: Month as "YYYY-MM" or "YYYY-MM-DD". Required for "get",
            optional for "list_money_movements" and
            "list_money_movement_groups".

    Returns:
        Structured text with the requested month data.

    Raises:
        ToolError: If "get" is called without ``month``.
    """
    app = cast("AppContext", ctx.lifespan_context)
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    if action == "list":
        return await _list_months(app, budget_id)

    if action == "get":
        if month is None:
            msg = "action='get' requires 'month' parameter"
            raise ToolError(msg)
        return await _get_month(app, budget_id, month)

    if action == "list_money_movements":
        return await _list_money_movements(app, budget_id, month)

    # Last action: list_money_movement_groups
    return await _list_money_movement_groups(app, budget_id, month)
