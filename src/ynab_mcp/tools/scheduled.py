"""Scheduled transaction tools: list, detail, create/update, delete."""

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.converters import dollars_to_milliunits, format_dollars


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
