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

from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.client import YNABClient
from ynab_mcp.converters import dollars_to_milliunits, format_dollars
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
        lines.append(f"\n{group['name']}")
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


if __name__ == "__main__":
    mcp.run()
