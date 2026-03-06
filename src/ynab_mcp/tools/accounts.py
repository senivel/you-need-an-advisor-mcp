"""Account tools: list, detail, and create YNAB accounts."""

from typing import Literal

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.converters import dollars_to_milliunits, format_dollars


async def _list_accounts(
    app: AppContext,
    budget_id: str,
    info: str | None,
    *,
    include_closed: bool = False,
) -> str:
    """List all accounts in a YNAB budget.

    Args:
        app: The application context with client and cache.
        budget_id: Resolved budget UUID.
        info: Optional info message from budget resolution.
        include_closed: If True, include closed accounts in the list.

    Returns:
        Structured text with count header and account details.
    """
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


async def _get_account(
    app: AppContext,
    budget_id: str,
    info: str | None,
    *,
    account_id: str,
) -> str:
    """Get detailed information about a specific YNAB account.

    Args:
        app: The application context with client and cache.
        budget_id: Resolved budget UUID.
        info: Optional info message from budget resolution.
        account_id: The account UUID.

    Returns:
        Structured text with full account details.
    """
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


async def _create_account(  # noqa: PLR0913
    app: AppContext,
    budget_id: str,
    info: str | None,
    *,
    name: str,
    account_type: str,
    balance: float,
) -> str:
    """Create a new account in a YNAB budget.

    Args:
        app: The application context with client and cache.
        budget_id: Resolved budget UUID.
        info: Optional info message from budget resolution.
        name: Display name for the new account.
        account_type: Account type string.
        balance: Opening balance in dollars.

    Returns:
        Confirmation text with created account details.
    """
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


@mcp.tool
async def manage_accounts(  # noqa: PLR0913, PLR0917
    ctx: Context,
    action: Literal["list", "get", "create"],
    budget_id_or_name: str | None = None,
    include_closed: bool = False,  # noqa: FBT001, FBT002
    account_id: str | None = None,
    name: str | None = None,
    account_type: str | None = None,
    balance: float | None = None,
) -> str:
    """Manage YNAB accounts: list, get details, or create.

    Actions:
        list: List all accounts. Uses budget_id_or_name, include_closed.
        get: Get account details. Uses budget_id_or_name, account_id (required).
        create: Create account. Uses budget_id_or_name, name (required),
            account_type (required), balance (required).

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        action: The operation to perform.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.
        include_closed: If True, include closed accounts (list only).
        account_id: The account UUID (get only).
        name: Display name for the new account (create only).
        account_type: Account type (create only).
        balance: Opening balance in dollars (create only).

    Returns:
        Structured text with account information or confirmation.

    Raises:
        ToolError: If required parameters for the action are missing.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

    if action == "list":
        return await _list_accounts(app, budget_id, info, include_closed=include_closed)

    if action == "get":
        if account_id is None:
            msg = "account_id is required for action='get'"
            raise ToolError(msg)
        return await _get_account(app, budget_id, info, account_id=account_id)

    if name is None or account_type is None or balance is None:
        msg = "name, account_type, and balance are required for action='create'"
        raise ToolError(msg)
    return await _create_account(
        app, budget_id, info, name=name, account_type=account_type, balance=balance
    )
