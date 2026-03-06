"""Category tools: list, detail, create/update categories and groups."""

from typing import Any, Literal, cast

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.converters import dollars_to_milliunits, format_dollars, normalize_month


_GOAL_TYPE_LABELS: dict[str, str] = {
    "TB": "Target Balance",
    "TBD": "Target Balance by Date",
    "MF": "Monthly Funding",
    "NEED": "Needed for Spending",
    "DEBT": "Debt",
}
"""Human-readable labels for YNAB goal type codes."""

_MAX_GROUP_NAME_LENGTH = 50
"""Maximum character length for a category group name."""


def _format_goal_lines(cat: dict[str, Any]) -> list[str]:
    """Build goal-info lines for a category detail view.

    Args:
        cat: Category dict from the YNAB API response.

    Returns:
        List of formatted goal lines, or empty list if no goal.
    """
    if not cat.get("goal_type"):
        return []

    label = _GOAL_TYPE_LABELS.get(cat["goal_type"], cat["goal_type"])
    lines = [f"  Goal: {label}"]
    if cat.get("goal_target") is not None:
        lines.append(f"    Target: {format_dollars(cat['goal_target'])}")
    if cat.get("goal_target_month"):
        lines.append(f"    Target month: {cat['goal_target_month']}")
    if cat.get("goal_percentage_complete") is not None:
        lines.append(f"    Progress: {cat['goal_percentage_complete']}%")
    if cat.get("goal_months_to_budget") is not None:
        lines.append(f"    Months to budget: {cat['goal_months_to_budget']}")
    if cat.get("goal_under_funded") is not None:
        lines.append(f"    Under funded: {format_dollars(cat['goal_under_funded'])}")
    if cat.get("goal_overall_funded") is not None:
        lines.append(
            f"    Overall funded: {format_dollars(cat['goal_overall_funded'])}"
        )
    if cat.get("goal_overall_left") is not None:
        lines.append(f"    Overall left: {format_dollars(cat['goal_overall_left'])}")
    return lines


async def _list_categories(
    app: AppContext,
    budget_id: str,
    info: str | None,
    *,
    include_hidden: bool = False,
) -> str:
    """List all categories grouped by category group.

    Returns:
        Structured text with count header and indented hierarchy.
    """
    data = await app.client.get(f"/budgets/{budget_id}/categories")
    groups = data["category_groups"]
    lines: list[str] = []
    total_count = 0
    for group in groups:
        if group["deleted"]:
            continue
        if group["hidden"] and not include_hidden:
            continue
        cats = [c for c in group["categories"] if not c["deleted"]]
        if not include_hidden:
            cats = [c for c in cats if not c["hidden"]]
        if not cats:
            continue
        total_count += len(cats)
        lines.append(f"\n{group['name']} (ID: {group['id']})")
        for cat in cats:
            budget_line = (
                f"    Budgeted: {format_dollars(cat['budgeted'])} | "
                f"Activity: {format_dollars(cat['activity'])} | "
                f"Balance: {format_dollars(cat['balance'])}"
            )
            lines.extend((
                f"  - {cat['name']}",
                f"    ID: {cat['id']}",
                budget_line,
            ))
    if total_count == 0:
        result = "No categories found."
        if info:
            result = f"{info}\n\n{result}"
        return result
    header = f"{total_count} categories found:"
    result = header + "\n".join(lines)
    if info:
        result = f"{info}\n\n{result}"
    return result


async def _get_category(
    app: AppContext,
    budget_id: str,
    info: str | None,
    *,
    category_id: str,
) -> str:
    """Get detailed information about a specific category.

    Returns:
        Structured text with full category details.
    """
    data = await app.client.get(f"/budgets/{budget_id}/categories/{category_id}")
    cat = data["category"]
    lines = [f"Category: {cat['name']}"]
    if cat.get("category_group_name"):
        lines.append(f"  Group: {cat['category_group_name']}")
    lines.extend((
        f"  Budgeted: {format_dollars(cat['budgeted'])}",
        f"  Activity: {format_dollars(cat['activity'])}",
        f"  Balance: {format_dollars(cat['balance'])}",
    ))
    if cat.get("note"):
        lines.append(f"  Note: {cat['note']}")
    lines.extend(_format_goal_lines(cat))
    result = "\n".join(lines)
    if info:
        result = f"{info}\n\n{result}"
    return result


async def _create_category(  # noqa: PLR0913
    app: AppContext,
    budget_id: str,
    *,
    name: str,
    category_group_id: str | None = None,
    note: str | None = None,
    goal_target: float | None = None,
    goal_target_date: str | None = None,
) -> str:
    """Create a new category.

    Returns:
        Confirmation text with created category details.
    """
    body: dict[str, Any] = {"name": name}
    if category_group_id is not None:
        body["category_group_id"] = category_group_id
    if note is not None:
        body["note"] = note
    if goal_target is not None:
        body["goal_target"] = dollars_to_milliunits(goal_target)
    if goal_target_date is not None:
        body["goal_target_date"] = goal_target_date
    data = await app.client.post(
        f"/budgets/{budget_id}/categories",
        json={"category": body},
    )
    cat = data["category"]
    return f"Category created:\n  Name: {cat['name']}\n  ID: {cat['id']}"


async def _update_category(  # noqa: PLR0913
    app: AppContext,
    budget_id: str,
    *,
    category_id: str,
    name: str | None = None,
    note: str | None = None,
    goal_target: float | None = None,
    goal_target_date: str | None = None,
) -> str:
    """Update an existing category.

    Returns:
        Confirmation text with updated category details.
    """
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if note is not None:
        body["note"] = note
    if goal_target is not None:
        body["goal_target"] = dollars_to_milliunits(goal_target)
    if goal_target_date is not None:
        body["goal_target_date"] = goal_target_date
    data = await app.client.patch(
        f"/budgets/{budget_id}/categories/{category_id}",
        json={"category": body},
    )
    cat = data["category"]
    return f"Category updated:\n  Name: {cat['name']}\n  ID: {cat['id']}"


async def _create_group(
    app: AppContext,
    budget_id: str,
    *,
    name: str,
) -> str:
    """Create a new category group.

    Returns:
        Confirmation text with created group details.

    Raises:
        ToolError: If name exceeds 50 characters.
    """
    if len(name) > _MAX_GROUP_NAME_LENGTH:
        msg = (
            f"Category group name must be {_MAX_GROUP_NAME_LENGTH} "
            f"characters or fewer (got {len(name)})."
        )
        raise ToolError(msg)
    data = await app.client.post(
        f"/budgets/{budget_id}/category_groups",
        json={"category_group": {"name": name}},
    )
    group = data["category_group"]
    return f"Category group created:\n  Name: {group['name']}\n  ID: {group['id']}"


async def _update_group(
    app: AppContext,
    budget_id: str,
    *,
    category_group_id: str,
    name: str,
) -> str:
    """Update an existing category group.

    Returns:
        Confirmation text with updated group details.

    Raises:
        ToolError: If name exceeds 50 characters.
    """
    if len(name) > _MAX_GROUP_NAME_LENGTH:
        msg = (
            f"Category group name must be {_MAX_GROUP_NAME_LENGTH} "
            f"characters or fewer (got {len(name)})."
        )
        raise ToolError(msg)
    data = await app.client.patch(
        f"/budgets/{budget_id}/category_groups/{category_group_id}",
        json={"category_group": {"name": name}},
    )
    group = data["category_group"]
    return f"Category group updated:\n  Name: {group['name']}\n  ID: {group['id']}"


async def _set_month_budget(
    app: AppContext,
    budget_id: str,
    *,
    category_id: str,
    month: str | None = None,
    budgeted: float | None = None,
) -> str:
    """Get or update the budgeted amount for a category in a specific month.

    Returns:
        Structured text with category budget details or confirmation.
    """
    normalized = normalize_month(month)
    path = f"/budgets/{budget_id}/months/{normalized}/categories/{category_id}"
    if budgeted is None:
        data = await app.client.get(path)
        cat = data["category"]
        lines = [
            f"Category: {cat['name']}",
            f"  Month: {normalized}",
            f"  Budgeted: {format_dollars(cat['budgeted'])}",
            f"  Activity: {format_dollars(cat['activity'])}",
            f"  Balance: {format_dollars(cat['balance'])}",
        ]
        lines.extend(_format_goal_lines(cat))
        return "\n".join(lines)
    milliunits = dollars_to_milliunits(budgeted)
    data = await app.client.patch(
        path,
        json={"category": {"budgeted": milliunits}},
    )
    cat = data["category"]
    return (
        f"Category budget updated:\n"
        f"  Category: {cat['name']}\n"
        f"  Month: {normalized}\n"
        f"  Budgeted: {format_dollars(budgeted)}"
    )


@mcp.tool
async def manage_categories(  # noqa: PLR0913, PLR0917, C901, PLR0911
    ctx: Context,
    action: Literal[
        "list",
        "get",
        "create",
        "update",
        "create_group",
        "update_group",
        "set_month_budget",
    ],
    budget_id_or_name: str | None = None,
    include_hidden: bool = False,  # noqa: FBT001, FBT002
    category_id: str | None = None,
    category_group_id: str | None = None,
    name: str | None = None,
    note: str | None = None,
    goal_target: float | None = None,
    goal_target_date: str | None = None,
    month: str | None = None,
    budgeted: float | None = None,
) -> str:
    """Manage YNAB categories: list, get, create, update, and budget by month.

    Actions:
        list: List all categories. Uses budget_id_or_name, include_hidden.
        get: Get category details. Uses category_id (required).
        create: Create category. Uses name (required), category_group_id, note,
            goal_target, goal_target_date.
        update: Update category. Uses category_id (required), name, note,
            goal_target, goal_target_date.
        create_group: Create category group. Uses name (required).
        update_group: Update category group. Uses category_group_id (required),
            name (required).
        set_month_budget: Get or set month budget. Uses category_id (required),
            month, budgeted (omit to get current value).

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        action: The operation to perform.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.
        include_hidden: If True, include hidden categories (list only).
        category_id: The category UUID (get, update, set_month_budget).
        category_group_id: Category group UUID (create, update_group).
        name: Name for category or group.
        note: Category note (create, update).
        goal_target: Goal target in dollars (create, update).
        goal_target_date: Goal target date (create, update).
        month: Month as YYYY-MM or YYYY-MM-DD (set_month_budget).
        budgeted: Budgeted amount in dollars (set_month_budget).

    Returns:
        Structured text with category information or confirmation.

    Raises:
        ToolError: If required parameters for the action are missing.
    """
    app = cast("AppContext", ctx.lifespan_context)
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

    if action == "list":
        return await _list_categories(
            app, budget_id, info, include_hidden=include_hidden
        )
    if action == "get":
        if category_id is None:
            msg = "category_id is required for action='get'"
            raise ToolError(msg)
        return await _get_category(app, budget_id, info, category_id=category_id)
    if action == "create":
        if name is None:
            msg = "name is required for action='create'"
            raise ToolError(msg)
        return await _create_category(
            app,
            budget_id,
            name=name,
            category_group_id=category_group_id,
            note=note,
            goal_target=goal_target,
            goal_target_date=goal_target_date,
        )
    if action == "update":
        if category_id is None:
            msg = "category_id is required for action='update'"
            raise ToolError(msg)
        return await _update_category(
            app,
            budget_id,
            category_id=category_id,
            name=name,
            note=note,
            goal_target=goal_target,
            goal_target_date=goal_target_date,
        )
    if action == "create_group":
        if name is None:
            msg = "name is required for action='create_group'"
            raise ToolError(msg)
        return await _create_group(app, budget_id, name=name)
    if action == "update_group":
        if category_group_id is None or name is None:
            msg = "category_group_id and name are required for action='update_group'"
            raise ToolError(msg)
        return await _update_group(
            app, budget_id, category_group_id=category_group_id, name=name
        )
    if category_id is None:
        msg = "category_id is required for action='set_month_budget'"
        raise ToolError(msg)
    return await _set_month_budget(
        app, budget_id, category_id=category_id, month=month, budgeted=budgeted
    )
