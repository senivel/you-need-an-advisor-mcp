"""Transaction tools: consolidated manage_transactions dispatch."""

from typing import Any, Literal, cast

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ynaa_mcp.app import AppContext, mcp
from ynaa_mcp.budget_resolver import resolve_budget
from ynaa_mcp.converters import dollars_to_milliunits, format_dollars, normalize_month


_CLEARED_INDICATORS: dict[str, str] = {
    "cleared": "[C]",
    "uncleared": "[U]",
    "reconciled": "[R]",
}
"""Compact status indicators for transaction list view."""


def _format_transaction_line(txn: dict[str, Any]) -> list[str]:
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


def _format_transaction_detail(txn: dict[str, Any]) -> list[str]:
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


def _format_transaction_confirmation(verb: str, txn: dict[str, Any]) -> str:
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


def _format_batch_result(data: dict[str, Any], verb: str) -> str:
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


async def _list_transactions(  # noqa: PLR0913, PLR0917, PLR0912, C901
    app: AppContext,
    budget_id: str,
    since_date: str | None,
    until_date: str | None,
    type: str | None,  # noqa: A002
    account_id: str | None,
    category_id: str | None,
    payee_id: str | None,
    month: str | None,
    limit: int | None,
) -> str:
    """List transactions with optional filtering.

    Args:
        app: The application context with client.
        budget_id: Resolved budget UUID.
        since_date: Only return transactions on or after this date.
        until_date: Only return transactions on or before this date.
        type: Filter by transaction type.
        account_id: Filter by account.
        category_id: Filter by category.
        payee_id: Filter by payee.
        month: Filter by month.
        limit: Maximum number of transactions to return.

    Returns:
        Structured text with transaction listings.

    Raises:
        ToolError: If more than one filter param is provided.
    """
    filters = [account_id, category_id, payee_id, month]
    active_filters = sum(1 for f in filters if f is not None)
    if active_filters > 1:
        msg = (
            "Only one filter (account, category, payee, or month) "
            "can be used at a time."
        )
        raise ToolError(msg)

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

    params: dict[str, str] = {}
    if since_date:
        params["since_date"] = since_date
    if type:
        params["type"] = type

    data = await app.client.get(path, params=params)
    transactions = data["transactions"]

    if until_date:
        transactions = [t for t in transactions if t["date"] <= until_date]

    if not transactions:
        return "No transactions found."

    total = len(transactions)

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


async def _get_transaction(
    app: AppContext,
    budget_id: str,
    transaction_id: str,
) -> str:
    """Get detailed information about a specific transaction.

    Returns:
        Structured text with full transaction detail view.
    """
    data = await app.client.get(f"/budgets/{budget_id}/transactions/{transaction_id}")
    txn = data["transaction"]
    lines = _format_transaction_detail(txn)
    return "\n".join(lines)


async def _create_transaction(  # noqa: PLR0913, PLR0917, C901
    app: AppContext,
    budget_id: str,
    account_id: str | None,
    date: str | None,
    amount: float | None,
    payee_name: str | None,
    payee_id: str | None,
    category_id: str | None,
    memo: str | None,
    cleared: str | None,
    approved: bool | None,  # noqa: FBT001
    flag_color: str | None,
) -> str:
    """Create a new transaction.

    Returns:
        Confirmation text.

    Raises:
        ToolError: If required fields are missing.
    """
    missing: list[str] = []
    if account_id is None:
        missing.append("account_id")
    if date is None:
        missing.append("date")
    if amount is None:
        missing.append("amount")
    if missing:
        msg = f"Create requires: {', '.join(missing)}"
        raise ToolError(msg)

    # Narrowing: pyright can't track list-based None checks, assert after guard
    assert account_id is not None
    assert date is not None
    assert amount is not None

    optional_fields: dict[str, Any] = {}
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

    body: dict[str, Any] = {
        "account_id": account_id,
        "date": date,
        "amount": dollars_to_milliunits(amount),
        **optional_fields,
    }

    data = await app.client.post(
        f"/budgets/{budget_id}/transactions",
        json={"transaction": body},
    )
    txn = data["transaction"]
    return _format_transaction_confirmation("created", txn)


async def _update_transaction(  # noqa: PLR0913, PLR0917, C901
    app: AppContext,
    budget_id: str,
    transaction_id: str,
    account_id: str | None,
    date: str | None,
    amount: float | None,
    payee_name: str | None,
    payee_id: str | None,
    category_id: str | None,
    memo: str | None,
    cleared: str | None,
    approved: bool | None,  # noqa: FBT001
    flag_color: str | None,
) -> str:
    """Update an existing transaction.

    Returns:
        Confirmation text.
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
    if cleared is not None:
        optional_fields["cleared"] = cleared
    if approved is not None:
        optional_fields["approved"] = approved
    if flag_color is not None:
        optional_fields["flag_color"] = flag_color

    body: dict[str, Any] = {**optional_fields}
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


async def _delete_transaction(
    app: AppContext,
    budget_id: str,
    transaction_id: str,
) -> str:
    """Delete a transaction.

    Returns:
        Confirmation text.
    """
    data = await app.client.delete(
        f"/budgets/{budget_id}/transactions/{transaction_id}",
    )
    txn = data["transaction"]
    return _format_transaction_confirmation("deleted", txn)


async def _batch_create_transactions(
    app: AppContext,
    budget_id: str,
    transactions: list[dict[str, Any]] | None,
) -> str:
    """Create multiple transactions in a single API call.

    Returns:
        Summary with count of created transactions and their IDs.

    Raises:
        ToolError: If transactions list is empty or None.
    """
    if not transactions:
        msg = "Transactions list must not be empty."
        raise ToolError(msg)

    processed: list[dict[str, Any]] = []
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


async def _batch_update_transactions(
    app: AppContext,
    budget_id: str,
    transactions: list[dict[str, Any]] | None,
) -> str:
    """Update multiple transactions in a single API call.

    Returns:
        Summary with count of updated transactions and their IDs.

    Raises:
        ToolError: If transactions list is empty or None.
    """
    if not transactions:
        msg = "Transactions list must not be empty."
        raise ToolError(msg)

    processed: list[dict[str, Any]] = []
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


async def _import_transactions(app: AppContext, budget_id: str) -> str:
    """Trigger import of transactions from linked accounts.

    Returns:
        Summary of imported transactions, or message if none imported.
    """
    data = await app.client.post(f"/budgets/{budget_id}/transactions/import")
    txn_ids = data.get("transaction_ids", [])

    if not txn_ids:
        return "No transactions to import."

    count = len(txn_ids)
    noun = "transaction" if count == 1 else "transactions"
    lines = [f"{count} {noun} imported:"]
    lines.extend(f"  - {txn_id}" for txn_id in txn_ids)
    return "\n".join(lines)


@mcp.tool
async def manage_transactions(  # noqa: PLR0913, PLR0917, C901, PLR0911
    ctx: Context,
    action: Literal[
        "list",
        "get",
        "create",
        "update",
        "delete",
        "batch_create",
        "batch_update",
        "import",
    ],
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
    since_date: str | None = None,
    until_date: str | None = None,
    type: str | None = None,  # noqa: A002
    month: str | None = None,
    limit: int | None = None,
    transactions: list[dict[str, Any]] | None = None,
) -> str:
    """Manage YNAB transactions: list, get, create, update, delete, batch, import.

    Dispatches to the appropriate action based on the ``action`` parameter.

    Actions:
        list: List transactions with optional filtering.
            Params: budget_id_or_name, since_date, until_date, type,
            account_id, category_id, payee_id, month, limit.
            Only one of account_id/category_id/payee_id/month at a time.
        get: Get full detail for a transaction.
            Params: budget_id_or_name, transaction_id (required).
        create: Create a new transaction.
            Params: budget_id_or_name, account_id (required), date (required),
            amount (required), payee_name, payee_id, category_id, memo,
            cleared, approved, flag_color.
        update: Update an existing transaction.
            Params: budget_id_or_name, transaction_id (required),
            plus any optional fields to change.
        delete: Delete a transaction.
            Params: budget_id_or_name, transaction_id (required).
        batch_create: Create multiple transactions at once.
            Params: budget_id_or_name, transactions (required, list[dict]).
        batch_update: Update multiple transactions at once.
            Params: budget_id_or_name, transactions (required, list[dict]).
        import: Import transactions from linked bank accounts.
            Params: budget_id_or_name only.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        action: The operation to perform.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        transaction_id: Transaction UUID (required for get, update, delete).
        account_id: Account UUID (required for create, filter for list).
        date: Transaction date as ISO string (required for create).
        amount: Amount in dollars (required for create, converted to milliunits).
        payee_name: Payee display name.
        payee_id: Payee UUID (filter for list, field for create/update).
        category_id: Category UUID (filter for list, field for create/update).
        memo: Transaction memo.
        cleared: Cleared status ("cleared", "uncleared", "reconciled").
        approved: Whether the transaction is approved.
        flag_color: Flag color for the transaction.
        since_date: Only return transactions on or after this date (list only).
        until_date: Only return transactions on or before this date (list only).
        type: Filter by type ("uncategorized" or "unapproved", list only).
        month: Filter by month (list only, "YYYY-MM" or "YYYY-MM-DD").
        limit: Maximum number of transactions to return (list only).
        transactions: List of transaction dicts (batch_create/batch_update only).

    Returns:
        Structured text with the requested transaction data.

    Raises:
        ToolError: If required parameters for the action are missing.
    """
    app = cast("AppContext", ctx.lifespan_context)
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    if action == "list":
        return await _list_transactions(
            app,
            budget_id,
            since_date,
            until_date,
            type,
            account_id,
            category_id,
            payee_id,
            month,
            limit,
        )

    if action == "get":
        if transaction_id is None:
            msg = "action='get' requires 'transaction_id'"
            raise ToolError(msg)
        return await _get_transaction(app, budget_id, transaction_id)

    if action == "create":
        return await _create_transaction(
            app,
            budget_id,
            account_id,
            date,
            amount,
            payee_name,
            payee_id,
            category_id,
            memo,
            cleared,
            approved,
            flag_color,
        )

    if action == "update":
        if transaction_id is None:
            msg = "action='update' requires 'transaction_id'"
            raise ToolError(msg)
        return await _update_transaction(
            app,
            budget_id,
            transaction_id,
            account_id,
            date,
            amount,
            payee_name,
            payee_id,
            category_id,
            memo,
            cleared,
            approved,
            flag_color,
        )

    if action == "delete":
        if transaction_id is None:
            msg = "action='delete' requires 'transaction_id'"
            raise ToolError(msg)
        return await _delete_transaction(app, budget_id, transaction_id)

    if action == "batch_create":
        return await _batch_create_transactions(app, budget_id, transactions)

    if action == "batch_update":
        return await _batch_update_transactions(app, budget_id, transactions)

    # Last action: import
    return await _import_transactions(app, budget_id)
