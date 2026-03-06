"""Account tools: list, detail, and create YNAB accounts."""

from fastmcp import Context

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.converters import dollars_to_milliunits, format_dollars


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
