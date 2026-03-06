"""Transaction tools: list, detail, create/update, delete, batch, import."""

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget
from ynab_mcp.converters import dollars_to_milliunits, format_dollars, normalize_month


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
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

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
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

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
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

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
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    data = await app.client.delete(
        f"/budgets/{budget_id}/transactions/{transaction_id}",
    )
    txn = data["transaction"]
    return _format_transaction_confirmation("deleted", txn)


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
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

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
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

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
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    data = await app.client.post(f"/budgets/{budget_id}/transactions/import")
    txn_ids = data.get("transaction_ids", [])

    if not txn_ids:
        return "No transactions to import."

    count = len(txn_ids)
    noun = "transaction" if count == 1 else "transactions"
    lines = [f"{count} {noun} imported:"]
    lines.extend(f"  - {txn_id}" for txn_id in txn_ids)
    return "\n".join(lines)
