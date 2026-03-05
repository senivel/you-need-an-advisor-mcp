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


_CLEARED_INDICATORS: dict[str, str] = {
    "cleared": "[C]",
    "uncleared": "[U]",
    "reconciled": "[R]",
}
"""Compact status indicators for transaction list view."""


def _format_transaction_line(txn: dict) -> list[str]:
    """Format a single transaction for list view.

    Each transaction produces two lines: a summary line with date, payee,
    amount, category, and cleared status, followed by the transaction ID.

    Args:
        txn: Transaction dict from the YNAB API response.

    Returns:
        Two-element list: summary line and ID line.
    """
    status = _CLEARED_INDICATORS.get(txn.get("cleared", ""), "")
    payee = txn.get("payee_name") or "(no payee)"
    category = txn.get("category_name") or "(no category)"
    amount = format_dollars(txn["amount"])
    return [
        f"- {txn['date']} | {payee} | {amount} | {category} {status}",
        f"  ID: {txn['id']}",
    ]


@mcp.tool
async def list_transactions(  # noqa: PLR0913, PLR0917, C901, PLR0912
    ctx: Context,
    budget_id_or_name: str = "last-used",
    since_date: str | None = None,
    until_date: str | None = None,
    type: str | None = None,  # noqa: A002
    account_id: str | None = None,
    category_id: str | None = None,
    payee_id: str | None = None,
    month: str | None = None,
    limit: int | None = None,
) -> str:
    """List transactions in a YNAB budget with optional filtering.

    Routes to different YNAB API endpoints based on which filter param
    is provided. Only one of ``account_id``, ``category_id``, ``payee_id``,
    or ``month`` may be specified at a time.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        since_date: Only return transactions on or after this date (ISO).
        until_date: Only return transactions on or before this date (ISO,
            applied client-side).
        type: Filter by transaction type ("uncategorized" or "unapproved").
        account_id: Filter by account (routes to account transactions endpoint).
        category_id: Filter by category (routes to category transactions endpoint).
        payee_id: Filter by payee (routes to payee transactions endpoint).
        month: Filter by month (routes to month transactions endpoint).
        limit: Maximum number of transactions to return.

    Returns:
        Structured text with count header and transaction lines,
        or "No transactions found." if none match.

    Raises:
        ToolError: If more than one filter param is provided.
    """
    # Validate mutual exclusivity
    filters = [account_id, category_id, payee_id, month]
    active_filters = sum(1 for f in filters if f is not None)
    if active_filters > 1:
        msg = (
            "Only one filter (account, category, payee, or month) "
            "can be used at a time."
        )
        raise ToolError(msg)

    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    # Determine API path based on filter
    if account_id:
        path = f"/budgets/{budget_id}/accounts/{account_id}/transactions"
    elif category_id:
        path = f"/budgets/{budget_id}/categories/{category_id}/transactions"
    elif payee_id:
        path = f"/budgets/{budget_id}/payees/{payee_id}/transactions"
    elif month:
        normalized = normalize_month(month)
        path = f"/budgets/{budget_id}/months/{normalized}/transactions"
    else:
        path = f"/budgets/{budget_id}/transactions"

    # Build query params
    params: dict[str, str] = {}
    if since_date:
        params["since_date"] = since_date
    if type:
        params["type"] = type

    data = await app.client.get(path, params=params)
    transactions = data["transactions"]

    # Client-side until_date filter
    if until_date:
        transactions = [t for t in transactions if t["date"] <= until_date]

    if not transactions:
        return "No transactions found."

    total = len(transactions)

    # Apply limit
    if limit and total > limit:
        header = f"Showing {limit} of {total} transactions:"
        transactions = transactions[:limit]
    else:
        noun = "transaction" if total == 1 else "transactions"
        header = f"{total} {noun} found:"

    lines = [header]
    for txn in transactions:
        lines.extend(_format_transaction_line(txn))

    return "\n".join(lines)


def _format_transaction_detail(txn: dict) -> list[str]:
    """Format a single transaction for detail view.

    Includes all fields with optional ones only shown when present.
    Subtransactions are displayed as an indented list.

    Args:
        txn: Transaction dict from the YNAB API response.

    Returns:
        List of formatted lines for the detail view.
    """
    lines = [
        f"Transaction: {txn.get('payee_name') or '(no payee)'}",
        f"  ID: {txn['id']}",
        f"  Date: {txn['date']}",
        f"  Amount: {format_dollars(txn['amount'])}",
        f"  Account: {txn['account_name']}",
        f"  Category: {txn.get('category_name') or '(none)'}",
        f"  Status: {txn['cleared']}",
        f"  Approved: {'Yes' if txn['approved'] else 'No'}",
    ]
    if txn.get("memo"):
        lines.append(f"  Memo: {txn['memo']}")
    if txn.get("flag_color"):
        lines.append(f"  Flag: {txn['flag_color']}")
    if txn.get("transfer_account_id"):
        lines.append(f"  Transfer account: {txn['transfer_account_id']}")

    subtxns = txn.get("subtransactions", [])
    if subtxns:
        lines.append(f"  Split ({len(subtxns)} items):")
        for sub in subtxns:
            sub_cat = sub.get("category_name") or "(no category)"
            lines.append(f"    - {format_dollars(sub['amount'])} | {sub_cat}")
            if sub.get("memo"):
                lines.append(f"      Memo: {sub['memo']}")
    return lines


@mcp.tool
async def get_transaction(
    ctx: Context,
    transaction_id: str,
    budget_id_or_name: str = "last-used",
) -> str:
    """Get detailed information about a specific YNAB transaction.

    Returns all transaction fields including payee, amount, account,
    category, cleared status, approval, and optional fields (memo,
    flag, transfer). Subtransactions are shown as an indented list.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        transaction_id: The transaction UUID.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Structured text with full transaction detail view.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.get(f"/budgets/{budget_id}/transactions/{transaction_id}")
    txn = data["transaction"]

    lines = _format_transaction_detail(txn)
    return "\n".join(lines)


@mcp.tool
async def manage_transaction(  # noqa: PLR0913, PLR0917, C901, PLR0912
    ctx: Context,
    budget_id_or_name: str = "last-used",
    transaction_id: str | None = None,
    account_id: str | None = None,
    date: str | None = None,
    amount: float | None = None,
    payee_name: str | None = None,
    payee_id: str | None = None,
    category_id: str | None = None,
    memo: str | None = None,
    cleared: str | None = None,
    approved: bool | None = None,  # noqa: FBT001
    flag_color: str | None = None,
) -> str:
    """Create or update a YNAB transaction.

    Without ``transaction_id``: creates a new transaction (POST).
    Requires ``account_id``, ``date``, and ``amount``.
    With ``transaction_id``: updates an existing transaction (PUT),
    only sending fields that are not None.

    Dollar amounts for ``amount`` are converted to YNAB milliunits.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        transaction_id: If provided, update this transaction. If None, create new.
        account_id: Account UUID (required for create).
        date: Transaction date as ISO string (required for create).
        amount: Transaction amount in dollars (required for create, converted
            to milliunits).
        payee_name: Payee display name.
        payee_id: Payee UUID.
        category_id: Category UUID.
        memo: Transaction memo.
        cleared: Cleared status ("cleared", "uncleared", "reconciled").
        approved: Whether the transaction is approved.
        flag_color: Flag color for the transaction.

    Returns:
        Confirmation text with key transaction fields.

    Raises:
        ToolError: If creating without required fields (account_id, date, amount).
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    # Optional fields shared between create and update
    optional_fields: dict[str, str | bool] = {}
    if payee_name is not None:
        optional_fields["payee_name"] = payee_name
    if payee_id is not None:
        optional_fields["payee_id"] = payee_id
    if category_id is not None:
        optional_fields["category_id"] = category_id
    if memo is not None:
        optional_fields["memo"] = memo
    if cleared is not None:
        optional_fields["cleared"] = cleared
    if approved is not None:
        optional_fields["approved"] = approved
    if flag_color is not None:
        optional_fields["flag_color"] = flag_color

    if transaction_id is None:
        # CREATE mode
        missing = []
        if account_id is None:
            missing.append("account_id")
        if date is None:
            missing.append("date")
        if amount is None:
            missing.append("amount")
        if missing:
            msg = f"Create requires: {', '.join(missing)}"
            raise ToolError(msg)

        body: dict = {
            "account_id": account_id,
            "date": date,
            "amount": dollars_to_milliunits(amount),  # type: ignore[arg-type]
            **optional_fields,
        }

        data = await app.client.post(
            f"/budgets/{budget_id}/transactions",
            json={"transaction": body},
        )
        txn = data["transaction"]
        return _format_transaction_confirmation("created", txn)

    # UPDATE mode
    body = {**optional_fields}
    if amount is not None:
        body["amount"] = dollars_to_milliunits(amount)
    if date is not None:
        body["date"] = date
    if account_id is not None:
        body["account_id"] = account_id

    data = await app.client.put(
        f"/budgets/{budget_id}/transactions/{transaction_id}",
        json={"transaction": body},
    )
    txn = data["transaction"]
    return _format_transaction_confirmation("updated", txn)


def _format_transaction_confirmation(verb: str, txn: dict) -> str:
    """Format a transaction create/update/delete confirmation.

    Args:
        verb: Action word ("created", "updated", "deleted").
        txn: Transaction dict from the YNAB API response.

    Returns:
        Confirmation string with key transaction fields.
    """
    payee = txn.get("payee_name") or "(no payee)"
    category = txn.get("category_name") or "(no category)"
    lines = [
        f"Transaction {verb}:",
        f"  ID: {txn['id']}",
        f"  Date: {txn['date']}",
        f"  Payee: {payee}",
        f"  Amount: {format_dollars(txn['amount'])}",
        f"  Category: {category}",
    ]
    return "\n".join(lines)


@mcp.tool
async def delete_transaction(
    ctx: Context,
    transaction_id: str,
    budget_id_or_name: str = "last-used",
) -> str:
    """Delete a YNAB transaction.

    Sends a DELETE request for the specified transaction and returns
    a confirmation with the deleted transaction's key fields.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        transaction_id: The transaction UUID to delete.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Confirmation text with deleted transaction details.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.delete(
        f"/budgets/{budget_id}/transactions/{transaction_id}",
    )
    txn = data["transaction"]
    return _format_transaction_confirmation("deleted", txn)


def _format_batch_result(data: dict, verb: str) -> str:
    """Format a batch transaction create/update response.

    Args:
        data: Response dict from the YNAB API with transaction_ids
            and optionally duplicate_import_ids.
        verb: Action word ("created" or "updated").

    Returns:
        Summary string with count header, per-ID lines, and duplicate IDs.
    """
    txn_ids = data.get("transaction_ids", [])
    count = len(txn_ids)
    noun = "transaction" if count == 1 else "transactions"
    lines = [f"{count} {noun} {verb}:"]
    lines.extend(f"  - {txn_id}" for txn_id in txn_ids)

    dup_ids = data.get("duplicate_import_ids", [])
    if dup_ids:
        lines.append(f"\n{len(dup_ids)} duplicate(s) skipped:")
        lines.extend(f"  - {dup_id}" for dup_id in dup_ids)

    return "\n".join(lines)


@mcp.tool
async def batch_create_transactions(
    ctx: Context,
    transactions: list[dict],
    budget_id_or_name: str = "last-used",
) -> str:
    """Create multiple YNAB transactions in a single API call.

    Each transaction dict should contain fields matching the YNAB API
    (account_id, date, amount, etc.). Dollar amounts in ``amount``
    fields are automatically converted to milliunits.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        transactions: List of transaction dicts to create.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Summary with count of created transactions and their IDs.

    Raises:
        ToolError: If transactions list is empty.
    """
    if not transactions:
        msg = "Transactions list must not be empty."
        raise ToolError(msg)

    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    processed = []
    for txn in transactions:
        txn_copy = dict(txn)
        if "amount" in txn_copy:
            txn_copy["amount"] = dollars_to_milliunits(txn_copy["amount"])
        processed.append(txn_copy)

    data = await app.client.post(
        f"/budgets/{budget_id}/transactions",
        json={"transactions": processed},
    )
    return _format_batch_result(data, "created")


@mcp.tool
async def batch_update_transactions(
    ctx: Context,
    transactions: list[dict],
    budget_id_or_name: str = "last-used",
) -> str:
    """Update multiple YNAB transactions in a single API call.

    Each transaction dict must include an ``id`` field. Dollar amounts
    in ``amount`` fields are automatically converted to milliunits.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        transactions: List of transaction dicts with IDs to update.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Summary with count of updated transactions and their IDs.

    Raises:
        ToolError: If transactions list is empty.
    """
    if not transactions:
        msg = "Transactions list must not be empty."
        raise ToolError(msg)

    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    processed = []
    for txn in transactions:
        txn_copy = dict(txn)
        if "amount" in txn_copy:
            txn_copy["amount"] = dollars_to_milliunits(txn_copy["amount"])
        processed.append(txn_copy)

    data = await app.client.patch(
        f"/budgets/{budget_id}/transactions",
        json={"transactions": processed},
    )
    return _format_batch_result(data, "updated")


@mcp.tool
async def import_transactions(
    ctx: Context,
    budget_id_or_name: str = "last-used",
) -> str:
    """Trigger import of transactions from linked accounts.

    Calls the YNAB import endpoint which pulls transactions from
    linked financial institutions. Returns the count and IDs of
    newly imported transactions.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Summary of imported transactions, or message if none imported.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.post(f"/budgets/{budget_id}/transactions/import")
    txn_ids = data.get("transaction_ids", [])

    if not txn_ids:
        return "No transactions to import."

    count = len(txn_ids)
    noun = "transaction" if count == 1 else "transactions"
    lines = [f"{count} {noun} imported:"]
    lines.extend(f"  - {txn_id}" for txn_id in txn_ids)
    return "\n".join(lines)


def _format_scheduled_transaction_line(txn: dict) -> list[str]:
    """Format a single scheduled transaction for list view.

    Each transaction produces two lines: a summary line with next date
    (or first date), payee, amount, category, and frequency, followed
    by the transaction ID.

    Args:
        txn: Scheduled transaction dict from the YNAB API response.

    Returns:
        Two-element list: summary line and ID line.
    """
    display_date = txn.get("date_next") or txn.get("date_first", "")
    payee = txn.get("payee_name") or "(no payee)"
    category = txn.get("category_name") or "(no category)"
    amount = format_dollars(txn["amount"])
    frequency = txn.get("frequency", "")
    return [
        f"- {display_date} | {payee} | {amount} | {category} [{frequency}]",
        f"  ID: {txn['id']}",
    ]


def _format_scheduled_transaction_detail(txn: dict) -> list[str]:
    """Format a single scheduled transaction for detail view.

    Includes all fields with optional ones only shown when present.
    Subtransactions are displayed as an indented list.

    Args:
        txn: Scheduled transaction dict from the YNAB API response.

    Returns:
        List of formatted lines for the detail view.
    """
    payee = txn.get("payee_name") or "(no payee)"
    lines = [
        f"Scheduled: {payee}",
        f"  ID: {txn['id']}",
        f"  Amount: {format_dollars(txn['amount'])}",
        f"  Account: {txn['account_name']}",
        f"  Category: {txn.get('category_name') or '(none)'}",
        f"  Frequency: {txn['frequency']}",
        f"  First date: {txn['date_first']}",
    ]
    if txn.get("date_next"):
        lines.append(f"  Next date: {txn['date_next']}")
    if txn.get("memo"):
        lines.append(f"  Memo: {txn['memo']}")
    if txn.get("flag_color"):
        lines.append(f"  Flag: {txn['flag_color']}")

    subtxns = txn.get("subtransactions", [])
    if subtxns:
        lines.append(f"  Split ({len(subtxns)} items):")
        for sub in subtxns:
            sub_cat = sub.get("category_name") or "(no category)"
            lines.append(f"    - {format_dollars(sub['amount'])} | {sub_cat}")
            if sub.get("memo"):
                lines.append(f"      Memo: {sub['memo']}")
    return lines


def _format_scheduled_transaction_confirmation(verb: str, txn: dict) -> str:
    """Format a scheduled transaction create/update/delete confirmation.

    Args:
        verb: Action word ("created", "updated", "deleted").
        txn: Scheduled transaction dict from the YNAB API response.

    Returns:
        Confirmation string with key scheduled transaction fields.
    """
    payee = txn.get("payee_name") or "(no payee)"
    lines = [
        f"Scheduled transaction {verb}:",
        f"  ID: {txn['id']}",
        f"  Payee: {payee}",
        f"  Amount: {format_dollars(txn['amount'])}",
        f"  Account: {txn['account_name']}",
        f"  Frequency: {txn.get('frequency', 'N/A')}",
    ]
    return "\n".join(lines)


@mcp.tool
async def list_scheduled_transactions(
    ctx: Context,
    budget_id_or_name: str = "last-used",
) -> str:
    """List all scheduled transactions in a YNAB budget.

    Returns a count header followed by each scheduled transaction's
    next date, payee, amount, category, and frequency. Deleted
    scheduled transactions are always excluded.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Structured text with count header and scheduled transaction lines,
        or "No scheduled transactions found." if none exist.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.get(f"/budgets/{budget_id}/scheduled_transactions")
    all_txns = data["scheduled_transactions"]

    # Exclude deleted
    txns = [t for t in all_txns if not t["deleted"]]

    if not txns:
        return "No scheduled transactions found."

    count = len(txns)
    noun = "scheduled transaction" if count == 1 else "scheduled transactions"
    lines = [f"{count} {noun} found:"]
    for txn in txns:
        lines.extend(_format_scheduled_transaction_line(txn))

    return "\n".join(lines)


@mcp.tool
async def get_scheduled_transaction(
    ctx: Context,
    scheduled_transaction_id: str,
    budget_id_or_name: str = "last-used",
) -> str:
    """Get detailed information about a specific scheduled transaction.

    Returns all scheduled transaction fields including payee, amount,
    account, category, frequency, first and next dates, and optional
    fields (memo, flag). Subtransactions are shown as an indented list.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        scheduled_transaction_id: The scheduled transaction UUID.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Structured text with full scheduled transaction detail view.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.get(
        f"/budgets/{budget_id}/scheduled_transactions/{scheduled_transaction_id}",
    )
    txn = data["scheduled_transaction"]

    lines = _format_scheduled_transaction_detail(txn)
    return "\n".join(lines)


@mcp.tool
async def manage_scheduled_transaction(  # noqa: PLR0913, PLR0917, C901, PLR0912
    ctx: Context,
    budget_id_or_name: str = "last-used",
    scheduled_transaction_id: str | None = None,
    account_id: str | None = None,
    date: str | None = None,
    amount: float | None = None,
    frequency: str | None = None,
    payee_name: str | None = None,
    payee_id: str | None = None,
    category_id: str | None = None,
    memo: str | None = None,
    flag_color: str | None = None,
) -> str:
    """Create or update a YNAB scheduled transaction.

    Without ``scheduled_transaction_id``: creates a new scheduled
    transaction (POST). Requires ``account_id`` and ``date``.
    With ``scheduled_transaction_id``: updates an existing scheduled
    transaction (PUT), only sending fields that are not None.

    Dollar amounts for ``amount`` are converted to YNAB milliunits.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        scheduled_transaction_id: If provided, update this scheduled
            transaction. If None, create new.
        account_id: Account UUID (required for create).
        date: Scheduled transaction date as ISO string (required for create).
        amount: Amount in dollars (converted to milliunits).
        frequency: Recurrence frequency (never, daily, weekly, everyOtherWeek,
            twiceAMonth, every4Weeks, monthly, everyOtherMonth,
            every3Months, every4Months, twiceAYear, yearly,
            everyOtherYear).
        payee_name: Payee display name.
        payee_id: Payee UUID.
        category_id: Category UUID.
        memo: Scheduled transaction memo.
        flag_color: Flag color for the scheduled transaction.

    Returns:
        Confirmation text with key scheduled transaction fields.

    Raises:
        ToolError: If creating without required fields (account_id, date).
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    # Optional fields shared between create and update
    optional_fields: dict[str, str | int] = {}
    if payee_name is not None:
        optional_fields["payee_name"] = payee_name
    if payee_id is not None:
        optional_fields["payee_id"] = payee_id
    if category_id is not None:
        optional_fields["category_id"] = category_id
    if memo is not None:
        optional_fields["memo"] = memo
    if flag_color is not None:
        optional_fields["flag_color"] = flag_color
    if frequency is not None:
        optional_fields["frequency"] = frequency

    if scheduled_transaction_id is None:
        # CREATE mode
        missing = []
        if account_id is None:
            missing.append("account_id")
        if date is None:
            missing.append("date")
        if missing:
            msg = f"Create requires: {', '.join(missing)}"
            raise ToolError(msg)

        body: dict = {
            "account_id": account_id,
            "date": date,
            **optional_fields,
        }
        if amount is not None:
            body["amount"] = dollars_to_milliunits(amount)

        data = await app.client.post(
            f"/budgets/{budget_id}/scheduled_transactions",
            json={"scheduled_transaction": body},
        )
        txn = data["scheduled_transaction"]
        return _format_scheduled_transaction_confirmation("created", txn)

    # UPDATE mode
    body = {**optional_fields}
    if amount is not None:
        body["amount"] = dollars_to_milliunits(amount)
    if date is not None:
        body["date"] = date
    if account_id is not None:
        body["account_id"] = account_id

    data = await app.client.put(
        f"/budgets/{budget_id}/scheduled_transactions/{scheduled_transaction_id}",
        json={"scheduled_transaction": body},
    )
    txn = data["scheduled_transaction"]
    return _format_scheduled_transaction_confirmation("updated", txn)


@mcp.tool
async def delete_scheduled_transaction(
    ctx: Context,
    scheduled_transaction_id: str,
    budget_id_or_name: str = "last-used",
) -> str:
    """Delete a YNAB scheduled transaction.

    Sends a DELETE request for the specified scheduled transaction
    and returns a confirmation with the deleted transaction's key fields.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        scheduled_transaction_id: The scheduled transaction UUID to delete.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Confirmation text with deleted scheduled transaction details.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.delete(
        f"/budgets/{budget_id}/scheduled_transactions/{scheduled_transaction_id}",
    )
    txn = data["scheduled_transaction"]
    return _format_scheduled_transaction_confirmation("deleted", txn)


if __name__ == "__main__":
    mcp.run()
