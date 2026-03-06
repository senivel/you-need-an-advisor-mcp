"""Month tools: list months, month detail, money movements."""

from fastmcp import Context

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.converters import format_dollars, normalize_month


@mcp.tool
async def list_months(
    ctx: Context,
    budget_id_or_name: str = "last-used",
) -> str:
    """List all budget months in a YNAB budget.

    Returns a count header followed by each month's income, budgeted,
    activity, to-be-budgeted, and age of money. Deleted months are
    always excluded.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Structured text with count header and month summaries,
        or "No months found." if none exist.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

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


@mcp.tool
async def get_month(
    ctx: Context,
    month: str,
    budget_id_or_name: str = "last-used",
) -> str:
    """Get detailed information about a specific budget month.

    Returns the month-level financial summary (income, budgeted,
    activity, to-be-budgeted, age of money) followed by categories
    grouped by category group. Each category shows budgeted, activity,
    and balance.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        month: Month as "YYYY-MM" or "YYYY-MM-DD".
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Structured text with month summary and grouped category detail.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

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
    groups: dict[str, list[dict]] = {}
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


@mcp.tool
async def list_money_movements(
    ctx: Context,
    budget_id_or_name: str = "last-used",
    month: str | None = None,
) -> str:
    """List money movements in a YNAB budget.

    Without ``month``: returns budget-wide money movements (all time).
    With ``month``: returns money movements for a specific month only.
    Each movement shows category name, group, allocation, spent, and income.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        month: If provided, scope to this month ("YYYY-MM" or "YYYY-MM-DD").

    Returns:
        Structured text with count header and movement lines,
        or "No money movements found." if none exist.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

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


@mcp.tool
async def list_money_movement_groups(
    ctx: Context,
    budget_id_or_name: str = "last-used",
    month: str | None = None,
) -> str:
    """List money movement groups in a YNAB budget.

    Without ``month``: returns budget-wide money movement groups (all time).
    With ``month``: returns money movement groups for a specific month only.
    Each group shows category group name, allocation, spent, and income.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        month: If provided, scope to this month ("YYYY-MM" or "YYYY-MM-DD").

    Returns:
        Structured text with count header and group lines,
        or "No money movement groups found." if none exist.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

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
