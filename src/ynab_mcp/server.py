"""FastMCP server for YNAB with lifespan-managed dependencies.

Provides the MCP server instance with:
- Lifespan-managed httpx client (created once, closed on shutdown)
- PAT validation at startup (fast-fail on bad auth)
- AppContext dataclass for sharing dependencies across tools
- Logging configured to stderr (stdout is MCP transport)
"""

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError

from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.client import YNABClient
from ynab_mcp.converters import dollars_to_milliunits, format_dollars, normalize_month
from ynab_mcp.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


@dataclass
class AppContext:
    """Shared dependencies for all MCP tools.

    Created during server lifespan and available to tools via
    ``ctx.lifespan_context``.

    Attributes:
        client: The YNAB API client instance.
    """

    client: YNABClient


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage server lifecycle: create client, validate auth, cleanup.

    Creates an httpx AsyncClient with YNAB base URL and Bearer auth,
    wraps it in a YNABClient with a RateLimiter, validates the PAT
    by calling GET /user, then yields the AppContext for tools.

    On exit, the httpx client is closed.

    Args:
        _server: The FastMCP server instance (required by protocol).

    Yields:
        AppContext with the authenticated YNAB client.

    Raises:
        RuntimeError: If YNAB_PAT environment variable is not set
            or if PAT validation fails.
    """
    token = os.environ.get("YNAB_PAT")
    if not token:
        logger.error("YNAB_PAT environment variable is not set")
        msg = (
            "YNAB_PAT environment variable is required. "
            "Set it to your YNAB Personal Access Token."
        )
        raise RuntimeError(msg)

    async with httpx.AsyncClient(
        base_url="https://api.ynab.com/v1",
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0),
    ) as http_client:
        rate_limiter = RateLimiter()
        client = YNABClient(http_client, rate_limiter)

        user_id = await client.validate_token()
        logger.info("Authenticated as user %s", user_id)

        yield AppContext(client=client)


mcp = FastMCP("YNAB", lifespan=lifespan)


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


@mcp.tool
async def get_accounts(
    ctx: Context,
    budget_id_or_name: str | None = None,
    include_closed: bool = False,  # noqa: FBT001, FBT002
) -> str:
    """List all accounts in a YNAB budget.

    Returns a count header followed by each account's name, type,
    and balance. Deleted accounts are always excluded. Closed
    accounts are excluded by default unless ``include_closed`` is True.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.
        include_closed: If True, include closed accounts in the list.

    Returns:
        Structured text with count header and account details,
        or a message if no accounts match the filter.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.get(f"/budgets/{budget_id}/accounts")
    all_accounts = data["accounts"]

    # Always exclude deleted
    accounts = [a for a in all_accounts if not a["deleted"]]
    had_accounts = len(accounts) > 0

    # Filter closed unless requested
    if not include_closed:
        accounts = [a for a in accounts if not a["closed"]]

    if not accounts:
        if had_accounts and not include_closed:
            msg = "No open accounts found."
        else:
            msg = "No accounts found."
        if info:
            msg = f"{info}\n\n{msg}"
        return msg

    count = len(accounts)
    noun = "account" if count == 1 else "accounts"
    lines = [f"{count} {noun} found:"]
    for a in accounts:
        lines.extend((
            f"- {a['name']}",
            f"  ID: {a['id']}",
            f"  Type: {a['type']}",
            f"  Balance: {format_dollars(a['balance'])}",
        ))

    result = "\n".join(lines)
    if info:
        result = f"{info}\n\n{result}"
    return result


@mcp.tool
async def get_account(
    ctx: Context,
    account_id: str,
    budget_id_or_name: str | None = None,
) -> str:
    """Get detailed information about a specific YNAB account.

    Returns all account fields including name, type, budget status,
    balances (formatted as dollars), note (if present), and closed status.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        account_id: The account UUID.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.

    Returns:
        Structured text with full account details.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.get(f"/budgets/{budget_id}/accounts/{account_id}")
    acct = data["account"]

    lines = [
        f"Account: {acct['name']}",
        f"  ID: {acct['id']}",
        f"  Type: {acct['type']}",
        f"  On budget: {'Yes' if acct['on_budget'] else 'No'}",
        f"  Closed: {'Yes' if acct['closed'] else 'No'}",
        f"  Balance: {format_dollars(acct['balance'])}",
        f"  Cleared balance: {format_dollars(acct['cleared_balance'])}",
        f"  Uncleared balance: {format_dollars(acct['uncleared_balance'])}",
    ]
    if acct.get("note"):
        lines.append(f"  Note: {acct['note']}")

    result = "\n".join(lines)
    if info:
        result = f"{info}\n\n{result}"
    return result


@mcp.tool
async def create_account(
    ctx: Context,
    name: str,
    account_type: str,
    balance: float,
    budget_id_or_name: str | None = None,
) -> str:
    """Create a new account in a YNAB budget.

    Accepts a dollar amount for the opening balance and converts it
    to YNAB milliunits before sending to the API.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        name: Display name for the new account.
        account_type: Account type (checking, savings, cash, creditCard,
            lineOfCredit, otherAsset, otherLiability, mortgage, autoLoan,
            studentLoan, personalLoan, medicalDebt, otherDebt).
        balance: Opening balance in dollars (converted to milliunits).
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.

    Returns:
        Confirmation text with created account details.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

    milliunits = dollars_to_milliunits(balance)
    data = await app.client.post(
        f"/budgets/{budget_id}/accounts",
        json={
            "account": {
                "name": name,
                "type": account_type,
                "balance": milliunits,
            }
        },
    )
    acct = data["account"]

    lines = [
        "Account created:",
        f"  Name: {acct['name']}",
        f"  Type: {acct['type']}",
        f"  Balance: {format_dollars(acct['balance'])}",
        f"  ID: {acct['id']}",
    ]

    result = "\n".join(lines)
    if info:
        result = f"{info}\n\n{result}"
    return result


_GOAL_TYPE_LABELS: dict[str, str] = {
    "TB": "Target Balance",
    "TBD": "Target Balance by Date",
    "MF": "Monthly Funding",
    "NEED": "Needed for Spending",
    "DEBT": "Debt",
}
"""Human-readable labels for YNAB goal type codes."""


@mcp.tool
async def get_categories(
    ctx: Context,
    budget_id_or_name: str | None = None,
    include_hidden: bool = False,  # noqa: FBT001, FBT002
) -> str:
    """List all categories in a YNAB budget grouped by category group.

    Returns a count header followed by an indented hierarchy of category
    groups and their categories with budgeted, activity, and balance amounts.
    Deleted groups and categories are always excluded. Hidden categories
    are excluded by default unless ``include_hidden`` is True.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.
        include_hidden: If True, include hidden categories in the list.

    Returns:
        Structured text with count header and indented hierarchy,
        or "No categories found." if none exist.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

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


def _format_goal_lines(cat: dict) -> list[str]:
    """Build goal-info lines for a category detail view.

    Only includes fields that are present (not None). Returns an
    empty list if the category has no goal set.

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


@mcp.tool
async def get_category(
    ctx: Context,
    category_id: str,
    budget_id_or_name: str | None = None,
) -> str:
    """Get detailed information about a specific YNAB category.

    Returns all category fields including name, group, budgeted, activity,
    balance, note (if present), and goal information (if a goal is set).
    All dollar amounts are formatted with ``$`` symbol and commas.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        category_id: The category UUID.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.

    Returns:
        Structured text with full category details and optional goal section.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.get(f"/budgets/{budget_id}/categories/{category_id}")
    cat = data["category"]

    lines = [
        f"Category: {cat['name']}",
    ]
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


_MAX_GROUP_NAME_LENGTH = 50
"""Maximum character length for a category group name."""


@mcp.tool
async def manage_category(  # noqa: PLR0913, PLR0917
    ctx: Context,
    name: str,
    budget_id_or_name: str | None = None,
    category_id: str | None = None,
    category_group_id: str | None = None,
    note: str | None = None,
    goal_target: float | None = None,
    goal_target_date: str | None = None,
) -> str:
    """Create or update a YNAB category.

    Without ``category_id``: creates a new category (POST).
    With ``category_id``: updates an existing category (PATCH),
    only sending fields that are not None.

    Dollar amounts for ``goal_target`` are converted to YNAB milliunits.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        name: Category name (required for create, optional field for update).
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.
        category_id: If provided, update this category. If None, create new.
        category_group_id: Parent category group UUID (for create).
        note: Optional category note.
        goal_target: Goal target in dollars (converted to milliunits).
        goal_target_date: Goal target date string.

    Returns:
        Confirmation text with created or updated category details.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    if category_id is None:
        # CREATE mode
        body: dict = {"name": name}
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

    # UPDATE mode
    body = {}
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


@mcp.tool
async def manage_category_group(
    ctx: Context,
    name: str,
    budget_id_or_name: str | None = None,
    category_group_id: str | None = None,
) -> str:
    """Create or update a YNAB category group.

    Without ``category_group_id``: creates a new group (POST).
    With ``category_group_id``: updates an existing group (PATCH).
    Name is validated to a maximum of 50 characters.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        name: Category group name (max 50 characters).
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.
        category_group_id: If provided, update this group. If None, create.

    Returns:
        Confirmation text with created or updated group details.

    Raises:
        ToolError: If name exceeds 50 characters.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    if len(name) > _MAX_GROUP_NAME_LENGTH:
        msg = (
            f"Category group name must be {_MAX_GROUP_NAME_LENGTH} "
            f"characters or fewer (got {len(name)})."
        )
        raise ToolError(msg)

    if category_group_id is None:
        # CREATE mode
        data = await app.client.post(
            f"/budgets/{budget_id}/category_groups",
            json={"category_group": {"name": name}},
        )
        group = data["category_group"]
        return f"Category group created:\n  Name: {group['name']}\n  ID: {group['id']}"

    # UPDATE mode
    data = await app.client.patch(
        f"/budgets/{budget_id}/category_groups/{category_group_id}",
        json={"category_group": {"name": name}},
    )
    group = data["category_group"]
    return f"Category group updated:\n  Name: {group['name']}\n  ID: {group['id']}"


@mcp.tool
async def month_category_budget(
    ctx: Context,
    category_id: str,
    budget_id_or_name: str | None = None,
    month: str | None = None,
    budgeted: float | None = None,
) -> str:
    """Get or update the budgeted amount for a category in a specific month.

    Without ``budgeted``: returns category budget info for the month (GET).
    With ``budgeted``: updates the budgeted amount (PATCH), converting
    dollars to milliunits. Month defaults to ``"current"`` when None.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        category_id: The category UUID.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.
        month: Month as ``"YYYY-MM"`` or ``"YYYY-MM-DD"``. Defaults to
            current month when None.
        budgeted: If provided, set the budgeted amount (in dollars) for
            this category in the given month.

    Returns:
        Structured text with category budget details (GET mode) or
        confirmation with updated amount (UPDATE mode).
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)
    normalized = normalize_month(month)
    path = f"/budgets/{budget_id}/months/{normalized}/categories/{category_id}"

    if budgeted is None:
        # GET mode
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

    # UPDATE mode
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


if __name__ == "__main__":
    mcp.run()
