"""Scheduled transaction tools: consolidated manage_scheduled_transactions."""

from typing import Any, Literal, cast

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.converters import dollars_to_milliunits, format_dollars


def _format_scheduled_transaction_line(txn: dict[str, Any]) -> list[str]:
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


def _format_scheduled_transaction_detail(txn: dict[str, Any]) -> list[str]:
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


def _format_scheduled_transaction_confirmation(verb: str, txn: dict[str, Any]) -> str:
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


async def _list_scheduled(app: AppContext, budget_id: str) -> str:
    """List all scheduled transactions, excluding deleted ones.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.

    Returns:
        Structured text with count header and scheduled transaction lines,
        or "No scheduled transactions found." if none exist.
    """
    data = await app.client.get(f"/budgets/{budget_id}/scheduled_transactions")
    all_txns = data["scheduled_transactions"]

    txns = [t for t in all_txns if not t["deleted"]]

    if not txns:
        return "No scheduled transactions found."

    count = len(txns)
    noun = "scheduled transaction" if count == 1 else "scheduled transactions"
    lines = [f"{count} {noun} found:"]
    for txn in txns:
        lines.extend(_format_scheduled_transaction_line(txn))

    return "\n".join(lines)


async def _get_scheduled(
    app: AppContext,
    budget_id: str,
    scheduled_transaction_id: str,
) -> str:
    """Get detailed information about a specific scheduled transaction.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.
        scheduled_transaction_id: The scheduled transaction UUID.

    Returns:
        Structured text with full scheduled transaction detail view.
    """
    data = await app.client.get(
        f"/budgets/{budget_id}/scheduled_transactions/{scheduled_transaction_id}",
    )
    txn = data["scheduled_transaction"]

    lines = _format_scheduled_transaction_detail(txn)
    return "\n".join(lines)


async def _create_scheduled(  # noqa: PLR0913, PLR0917, C901
    app: AppContext,
    budget_id: str,
    account_id: str | None,
    date: str | None,
    amount: float | None,
    frequency: str | None,
    payee_name: str | None,
    payee_id: str | None,
    category_id: str | None,
    memo: str | None,
    flag_color: str | None,
) -> str:
    """Create a new scheduled transaction.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.
        account_id: Account UUID (required).
        date: Scheduled transaction date (required).
        amount: Amount in dollars (converted to milliunits).
        frequency: Recurrence frequency.
        payee_name: Payee display name.
        payee_id: Payee UUID.
        category_id: Category UUID.
        memo: Memo text.
        flag_color: Flag color.

    Returns:
        Confirmation text with key scheduled transaction fields.

    Raises:
        ToolError: If required fields (account_id, date) are missing.
    """
    missing: list[str] = []
    if account_id is None:
        missing.append("account_id")
    if date is None:
        missing.append("date")
    if missing:
        msg = f"Create requires: {', '.join(missing)}"
        raise ToolError(msg)

    # Narrowing: pyright can't track list-based None checks, assert after guard
    assert account_id is not None
    assert date is not None

    optional_fields: dict[str, Any] = {}
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

    body: dict[str, Any] = {
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


async def _update_scheduled(  # noqa: PLR0913, PLR0917
    app: AppContext,
    budget_id: str,
    scheduled_transaction_id: str,
    account_id: str | None,
    date: str | None,
    amount: float | None,
    frequency: str | None,
    payee_name: str | None,
    payee_id: str | None,
    category_id: str | None,
    memo: str | None,
    flag_color: str | None,
) -> str:
    """Update an existing scheduled transaction.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.
        scheduled_transaction_id: The scheduled transaction UUID.
        account_id: Account UUID.
        date: Scheduled transaction date.
        amount: Amount in dollars (converted to milliunits).
        frequency: Recurrence frequency.
        payee_name: Payee display name.
        payee_id: Payee UUID.
        category_id: Category UUID.
        memo: Memo text.
        flag_color: Flag color.

    Returns:
        Confirmation text with key scheduled transaction fields.
    """
    optional_fields: dict[str, Any] = {}
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

    body: dict[str, Any] = {**optional_fields}
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


async def _delete_scheduled(
    app: AppContext,
    budget_id: str,
    scheduled_transaction_id: str,
) -> str:
    """Delete a scheduled transaction.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.
        scheduled_transaction_id: The scheduled transaction UUID.

    Returns:
        Confirmation text with deleted scheduled transaction details.
    """
    data = await app.client.delete(
        f"/budgets/{budget_id}/scheduled_transactions/{scheduled_transaction_id}",
    )
    txn = data["scheduled_transaction"]
    return _format_scheduled_transaction_confirmation("deleted", txn)


@mcp.tool
async def manage_scheduled_transactions(  # noqa: PLR0913, PLR0917
    ctx: Context,
    action: Literal["list", "get", "create", "update", "delete"],
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
    """Manage YNAB scheduled transactions: list, get, create, update, delete.

    Dispatches to the appropriate action based on the ``action`` parameter.

    Actions:
        list: List all scheduled transactions (excludes deleted).
            Params: budget_id_or_name.
        get: Get full detail for a scheduled transaction.
            Params: budget_id_or_name, scheduled_transaction_id (required).
        create: Create a new scheduled transaction.
            Params: budget_id_or_name, account_id (required), date (required),
            amount, frequency, payee_name, payee_id, category_id, memo,
            flag_color.
        update: Update an existing scheduled transaction.
            Params: budget_id_or_name, scheduled_transaction_id (required),
            plus any optional fields to change.
        delete: Delete a scheduled transaction.
            Params: budget_id_or_name, scheduled_transaction_id (required).

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        action: The operation to perform.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        scheduled_transaction_id: Scheduled transaction UUID (required for
            get, update, delete).
        account_id: Account UUID (required for create).
        date: Scheduled transaction date as ISO string (required for create).
        amount: Amount in dollars (converted to YNAB milliunits).
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
        Structured text with the requested scheduled transaction data.

    Raises:
        ToolError: If required parameters for the action are missing.
    """
    app = cast("AppContext", ctx.lifespan_context)
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    if action == "list":
        return await _list_scheduled(app, budget_id)

    if action == "get":
        if scheduled_transaction_id is None:
            msg = "action='get' requires 'scheduled_transaction_id'"
            raise ToolError(msg)
        return await _get_scheduled(app, budget_id, scheduled_transaction_id)

    if action == "create":
        return await _create_scheduled(
            app,
            budget_id,
            account_id,
            date,
            amount,
            frequency,
            payee_name,
            payee_id,
            category_id,
            memo,
            flag_color,
        )

    if action == "update":
        if scheduled_transaction_id is None:
            msg = "action='update' requires 'scheduled_transaction_id'"
            raise ToolError(msg)
        return await _update_scheduled(
            app,
            budget_id,
            scheduled_transaction_id,
            account_id,
            date,
            amount,
            frequency,
            payee_name,
            payee_id,
            category_id,
            memo,
            flag_color,
        )

    # Last action: delete
    if scheduled_transaction_id is None:
        msg = "action='delete' requires 'scheduled_transaction_id'"
        raise ToolError(msg)
    return await _delete_scheduled(app, budget_id, scheduled_transaction_id)
