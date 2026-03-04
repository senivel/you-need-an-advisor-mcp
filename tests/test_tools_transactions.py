"""Tests for transaction tools: list, get, manage, delete, batch, import."""

import pytest
from fastmcp.exceptions import ToolError

from ynab_mcp.server import (
    batch_create_transactions,
    batch_update_transactions,
    delete_transaction,
    get_transaction,
    import_transactions,
    list_transactions,
    manage_transaction,
)


@pytest.fixture
def mock_ctx(mocker):
    """Create a mock MCP Context with a mocked YNABClient.

    Returns:
        A mock Context with lifespan_context.client set.
    """
    client = mocker.AsyncMock()
    app = mocker.MagicMock()
    app.client = client
    ctx = mocker.MagicMock()
    ctx.lifespan_context = app
    return ctx


def _make_transaction(  # noqa: PLR0913
    *,
    txn_id="txn-001",
    date="2026-03-01",
    amount=-45.67,
    payee_name="Grocery Store",
    category_name="Groceries",
    account_name="Checking",
    account_id="acct-111",
    cleared="cleared",
    approved=True,
    memo=None,
    flag_color=None,
    transfer_account_id=None,
    subtransactions=None,
    deleted=False,
):
    """Build a sample transaction dict matching YNAB API shape (post-conversion).

    Returns:
        Dict with transaction fields.
    """
    return {
        "id": txn_id,
        "date": date,
        "amount": amount,
        "payee_name": payee_name,
        "category_name": category_name,
        "account_name": account_name,
        "account_id": account_id,
        "cleared": cleared,
        "approved": approved,
        "memo": memo,
        "flag_color": flag_color,
        "transfer_account_id": transfer_account_id,
        "subtransactions": subtransactions or [],
        "deleted": deleted,
    }


class TestListTransactions:
    """Tests for list_transactions tool."""

    @pytest.mark.anyio
    async def test_list_all(self, mock_ctx, mocker):
        """Count header, formatted lines with date|payee|amount|category [status]."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [
                _make_transaction(
                    txn_id="txn-001",
                    date="2026-03-01",
                    payee_name="Grocery Store",
                    amount=-45.67,
                    category_name="Groceries",
                    cleared="cleared",
                ),
                _make_transaction(
                    txn_id="txn-002",
                    date="2026-03-02",
                    payee_name="Coffee Shop",
                    amount=-5.50,
                    category_name="Dining Out",
                    cleared="uncleared",
                ),
            ],
        }

        result = await list_transactions(mock_ctx)

        assert "2 transactions found:" in result
        assert "2026-03-01" in result
        assert "Grocery Store" in result
        assert "-$45.67" in result
        assert "Groceries" in result
        assert "[C]" in result
        assert "Coffee Shop" in result
        assert "[U]" in result
        assert "ID: txn-001" in result
        assert "ID: txn-002" in result

    @pytest.mark.anyio
    async def test_filter_by_account(self, mock_ctx, mocker):
        """Routes to /accounts/{id}/transactions."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [_make_transaction()],
        }

        await list_transactions(mock_ctx, account_id="acct-111")

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert "/accounts/acct-111/transactions" in call_args[0][0]

    @pytest.mark.anyio
    async def test_filter_by_category(self, mock_ctx, mocker):
        """Routes to /categories/{id}/transactions."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [_make_transaction()],
        }

        await list_transactions(mock_ctx, category_id="cat-111")

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert "/categories/cat-111/transactions" in call_args[0][0]

    @pytest.mark.anyio
    async def test_filter_by_payee(self, mock_ctx, mocker):
        """Routes to /payees/{id}/transactions."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [_make_transaction()],
        }

        await list_transactions(mock_ctx, payee_id="payee-111")

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert "/payees/payee-111/transactions" in call_args[0][0]

    @pytest.mark.anyio
    async def test_filter_by_month(self, mock_ctx, mocker):
        """Routes to /months/{month}/transactions, normalizes month."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [_make_transaction()],
        }

        await list_transactions(mock_ctx, month="2026-03")

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert "/months/2026-03-01/transactions" in call_args[0][0]

    @pytest.mark.anyio
    async def test_since_date_query_param(self, mock_ctx, mocker):
        """since_date passed as query param to API."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [_make_transaction()],
        }

        await list_transactions(mock_ctx, since_date="2026-01-01")

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert call_args[1]["params"]["since_date"] == "2026-01-01"

    @pytest.mark.anyio
    async def test_until_date_client_side_filter(self, mock_ctx, mocker):
        """until_date filters client-side (transactions after excluded)."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [
                _make_transaction(txn_id="txn-001", date="2026-02-28"),
                _make_transaction(txn_id="txn-002", date="2026-03-01"),
                _make_transaction(txn_id="txn-003", date="2026-03-15"),
            ],
        }

        result = await list_transactions(mock_ctx, until_date="2026-03-01")

        assert "2 transactions found:" in result
        assert "txn-001" in result
        assert "txn-002" in result
        assert "txn-003" not in result

    @pytest.mark.anyio
    async def test_type_query_param(self, mock_ctx, mocker):
        """Type param (uncategorized, unapproved) passed as query param."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [_make_transaction()],
        }

        await list_transactions(mock_ctx, type="unapproved")

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert call_args[1]["params"]["type"] == "unapproved"

    @pytest.mark.anyio
    async def test_mutual_exclusivity(self, mock_ctx, mocker):
        """Mutually exclusive filters (>1) raises ToolError."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="Only one filter"):
            await list_transactions(
                mock_ctx, account_id="acct-111", category_id="cat-111"
            )

    @pytest.mark.anyio
    async def test_limit_truncates(self, mock_ctx, mocker):
        """Limit param truncates with 'Showing X of Y transactions' note."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [
                _make_transaction(txn_id=f"txn-{i:03d}", date=f"2026-03-{i:02d}")
                for i in range(1, 11)
            ],
        }

        result = await list_transactions(mock_ctx, limit=3)

        assert "Showing 3 of 10 transactions:" in result
        assert "txn-001" in result
        assert "txn-003" in result
        assert "txn-004" not in result

    @pytest.mark.anyio
    async def test_empty_result(self, mock_ctx, mocker):
        """Empty result returns 'No transactions found.'."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [],
        }

        result = await list_transactions(mock_ctx)

        assert result == "No transactions found."

    @pytest.mark.anyio
    async def test_no_payee_no_category(self, mock_ctx, mocker):
        """No payee shows '(no payee)', no category shows '(no category)'."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transactions": [
                _make_transaction(payee_name=None, category_name=None),
            ],
        }

        result = await list_transactions(mock_ctx)

        assert "(no payee)" in result
        assert "(no category)" in result


class TestGetTransaction:
    """Tests for get_transaction tool."""

    @pytest.mark.anyio
    async def test_full_detail_view(self, mock_ctx, mocker):
        """Returns full detail view with all fields."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transaction": _make_transaction(
                txn_id="txn-001",
                date="2026-03-01",
                payee_name="Grocery Store",
                amount=-45.67,
                category_name="Groceries",
                account_name="Checking",
                cleared="cleared",
                approved=True,
            ),
        }

        result = await get_transaction(mock_ctx, transaction_id="txn-001")

        assert "Transaction: Grocery Store" in result
        assert "ID: txn-001" in result
        assert "Date: 2026-03-01" in result
        assert "-$45.67" in result
        assert "Account: Checking" in result
        assert "Category: Groceries" in result
        assert "Status: cleared" in result
        assert "Approved: Yes" in result

    @pytest.mark.anyio
    async def test_shows_memo(self, mock_ctx, mocker):
        """Shows memo when present."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transaction": _make_transaction(memo="Weekly groceries"),
        }

        result = await get_transaction(mock_ctx, transaction_id="txn-001")

        assert "Memo: Weekly groceries" in result

    @pytest.mark.anyio
    async def test_shows_flag_color(self, mock_ctx, mocker):
        """Shows flag_color when present."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transaction": _make_transaction(flag_color="red"),
        }

        result = await get_transaction(mock_ctx, transaction_id="txn-001")

        assert "Flag: red" in result

    @pytest.mark.anyio
    async def test_shows_transfer_account(self, mock_ctx, mocker):
        """Shows transfer_account_id when present."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transaction": _make_transaction(
                transfer_account_id="acct-transfer-222",
            ),
        }

        result = await get_transaction(mock_ctx, transaction_id="txn-001")

        assert "Transfer account: acct-transfer-222" in result

    @pytest.mark.anyio
    async def test_subtransactions(self, mock_ctx, mocker):
        """Shows subtransactions as indented list with amount, category, memo."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transaction": _make_transaction(
                subtransactions=[
                    {
                        "amount": -30.00,
                        "category_name": "Groceries",
                        "memo": "Food items",
                    },
                    {
                        "amount": -15.67,
                        "category_name": "Household",
                        "memo": None,
                    },
                ],
            ),
        }

        result = await get_transaction(mock_ctx, transaction_id="txn-001")

        assert "Split (2 items):" in result
        assert "-$30.00 | Groceries" in result
        assert "Memo: Food items" in result
        assert "-$15.67 | Household" in result

    @pytest.mark.anyio
    async def test_no_payee_no_category(self, mock_ctx, mocker):
        """Handles transaction with no payee or category gracefully."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "transaction": _make_transaction(
                payee_name=None,
                category_name=None,
            ),
        }

        result = await get_transaction(mock_ctx, transaction_id="txn-001")

        assert "Transaction: (no payee)" in result
        assert "Category: (none)" in result


class TestManageTransaction:
    """Tests for manage_transaction tool (create/update)."""

    @pytest.mark.anyio
    async def test_create_sends_post(self, mock_ctx, mocker):
        """Create mode (no transaction_id) POSTs with {transaction: body}."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction": _make_transaction(
                txn_id="txn-new",
                date="2026-03-01",
                payee_name="Grocery Store",
                amount=-45.67,
                category_name="Groceries",
            ),
        }

        result = await manage_transaction(
            mock_ctx,
            account_id="acct-111",
            date="2026-03-01",
            amount=-45.67,
            payee_name="Grocery Store",
        )

        call_args = mock_ctx.lifespan_context.client.post.call_args
        assert "/budgets/budget-123/transactions" in call_args[0][0]
        body = call_args[1]["json"]["transaction"]
        assert body["account_id"] == "acct-111"
        assert body["date"] == "2026-03-01"
        assert "created" in result.lower()

    @pytest.mark.anyio
    async def test_create_converts_dollars_to_milliunits(self, mock_ctx, mocker):
        """Create mode converts amount dollars to milliunits."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction": _make_transaction(amount=-45.67),
        }

        await manage_transaction(
            mock_ctx,
            account_id="acct-111",
            date="2026-03-01",
            amount=-45.67,
        )

        call_args = mock_ctx.lifespan_context.client.post.call_args
        body = call_args[1]["json"]["transaction"]
        assert body["amount"] == -45670

    @pytest.mark.anyio
    async def test_create_includes_optional_fields(self, mock_ctx, mocker):
        """Create mode includes optional fields only when provided."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction": _make_transaction(),
        }

        await manage_transaction(
            mock_ctx,
            account_id="acct-111",
            date="2026-03-01",
            amount=-10.0,
            payee_name="Store",
            payee_id="payee-111",
            category_id="cat-111",
            memo="Test memo",
            cleared="cleared",
            approved=True,
            flag_color="red",
        )

        call_args = mock_ctx.lifespan_context.client.post.call_args
        body = call_args[1]["json"]["transaction"]
        assert body["payee_name"] == "Store"
        assert body["payee_id"] == "payee-111"
        assert body["category_id"] == "cat-111"
        assert body["memo"] == "Test memo"
        assert body["cleared"] == "cleared"
        assert body["approved"] is True
        assert body["flag_color"] == "red"

    @pytest.mark.anyio
    async def test_create_excludes_none_optional_fields(self, mock_ctx, mocker):
        """Create mode does not include None optional fields in body."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction": _make_transaction(),
        }

        await manage_transaction(
            mock_ctx,
            account_id="acct-111",
            date="2026-03-01",
            amount=-10.0,
        )

        call_args = mock_ctx.lifespan_context.client.post.call_args
        body = call_args[1]["json"]["transaction"]
        assert "payee_name" not in body
        assert "memo" not in body
        assert "flag_color" not in body

    @pytest.mark.anyio
    async def test_create_missing_account_id_raises(self, mock_ctx, mocker):
        """Create mode missing account_id raises ToolError."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="account_id"):
            await manage_transaction(
                mock_ctx,
                date="2026-03-01",
                amount=-10.0,
            )

    @pytest.mark.anyio
    async def test_create_missing_date_raises(self, mock_ctx, mocker):
        """Create mode missing date raises ToolError."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="date"):
            await manage_transaction(
                mock_ctx,
                account_id="acct-111",
                amount=-10.0,
            )

    @pytest.mark.anyio
    async def test_create_missing_amount_raises(self, mock_ctx, mocker):
        """Create mode missing amount raises ToolError."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="amount"):
            await manage_transaction(
                mock_ctx,
                account_id="acct-111",
                date="2026-03-01",
            )

    @pytest.mark.anyio
    async def test_update_sends_put(self, mock_ctx, mocker):
        """Update mode (with transaction_id) sends PUT with only provided fields."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.put.return_value = {
            "transaction": _make_transaction(
                txn_id="txn-001",
                memo="Updated memo",
            ),
        }

        result = await manage_transaction(
            mock_ctx,
            transaction_id="txn-001",
            memo="Updated memo",
        )

        call_args = mock_ctx.lifespan_context.client.put.call_args
        assert "/transactions/txn-001" in call_args[0][0]
        body = call_args[1]["json"]["transaction"]
        assert body["memo"] == "Updated memo"
        assert "account_id" not in body
        assert "updated" in result.lower()

    @pytest.mark.anyio
    async def test_update_converts_amount(self, mock_ctx, mocker):
        """Update mode converts amount to milliunits when provided."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.put.return_value = {
            "transaction": _make_transaction(amount=-25.0),
        }

        await manage_transaction(
            mock_ctx,
            transaction_id="txn-001",
            amount=-25.0,
        )

        call_args = mock_ctx.lifespan_context.client.put.call_args
        body = call_args[1]["json"]["transaction"]
        assert body["amount"] == -25000

    @pytest.mark.anyio
    async def test_create_returns_confirmation(self, mock_ctx, mocker):
        """Create mode returns confirmation with key fields."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction": _make_transaction(
                txn_id="txn-new",
                date="2026-03-01",
                payee_name="Grocery Store",
                amount=-45.67,
                category_name="Groceries",
            ),
        }

        result = await manage_transaction(
            mock_ctx,
            account_id="acct-111",
            date="2026-03-01",
            amount=-45.67,
            payee_name="Grocery Store",
        )

        assert "2026-03-01" in result
        assert "Grocery Store" in result
        assert "-$45.67" in result

    @pytest.mark.anyio
    async def test_update_returns_confirmation(self, mock_ctx, mocker):
        """Update mode returns confirmation with key fields."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.put.return_value = {
            "transaction": _make_transaction(
                txn_id="txn-001",
                date="2026-03-01",
                payee_name="Coffee Shop",
                amount=-5.50,
                category_name="Dining Out",
            ),
        }

        result = await manage_transaction(
            mock_ctx,
            transaction_id="txn-001",
            memo="Updated",
        )

        assert "2026-03-01" in result
        assert "Coffee Shop" in result
        assert "-$5.50" in result


class TestDeleteTransaction:
    """Tests for delete_transaction tool."""

    @pytest.mark.anyio
    async def test_delete_sends_delete(self, mock_ctx, mocker):
        """delete_transaction sends DELETE and returns confirmation."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.delete.return_value = {
            "transaction": _make_transaction(
                txn_id="txn-001",
                date="2026-03-01",
                payee_name="Grocery Store",
                amount=-45.67,
            ),
        }

        result = await delete_transaction(mock_ctx, transaction_id="txn-001")

        call_args = mock_ctx.lifespan_context.client.delete.call_args
        assert "/transactions/txn-001" in call_args[0][0]
        assert "deleted" in result.lower()
        assert "2026-03-01" in result
        assert "Grocery Store" in result
        assert "-$45.67" in result


class TestBatchCreateTransactions:
    """Tests for batch_create_transactions tool."""

    @pytest.mark.anyio
    async def test_batch_create_posts_with_converted_amounts(self, mock_ctx, mocker):
        """Converts amounts and POSTs with {transactions: [...]}."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction_ids": ["txn-001", "txn-002"],
            "duplicate_import_ids": [],
            "transactions": [],
        }

        await batch_create_transactions(
            mock_ctx,
            transactions=[
                {"account_id": "acct-1", "date": "2026-03-01", "amount": -10.50},
                {"account_id": "acct-1", "date": "2026-03-02", "amount": -25.00},
            ],
        )

        call_args = mock_ctx.lifespan_context.client.post.call_args
        assert "/budgets/budget-123/transactions" in call_args[0][0]
        txns = call_args[1]["json"]["transactions"]
        assert txns[0]["amount"] == -10500
        assert txns[1]["amount"] == -25000

    @pytest.mark.anyio
    async def test_batch_create_returns_summary(self, mock_ctx, mocker):
        """Returns summary count and per-transaction ID lines."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction_ids": ["txn-001", "txn-002"],
            "duplicate_import_ids": [],
            "transactions": [],
        }

        result = await batch_create_transactions(
            mock_ctx,
            transactions=[
                {"account_id": "acct-1", "date": "2026-03-01", "amount": -10.0},
                {"account_id": "acct-1", "date": "2026-03-02", "amount": -25.0},
            ],
        )

        assert "2" in result
        assert "created" in result.lower()
        assert "txn-001" in result
        assert "txn-002" in result

    @pytest.mark.anyio
    async def test_batch_create_empty_raises(self, mock_ctx, mocker):
        """Empty batch raises ToolError."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError):
            await batch_create_transactions(mock_ctx, transactions=[])

    @pytest.mark.anyio
    async def test_batch_create_includes_duplicate_ids(self, mock_ctx, mocker):
        """Includes duplicate_import_ids in response when present."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction_ids": ["txn-001"],
            "duplicate_import_ids": ["dup-001"],
            "transactions": [],
        }

        result = await batch_create_transactions(
            mock_ctx,
            transactions=[
                {"account_id": "acct-1", "date": "2026-03-01", "amount": -10.0},
            ],
        )

        assert "dup-001" in result


class TestBatchUpdateTransactions:
    """Tests for batch_update_transactions tool."""

    @pytest.mark.anyio
    async def test_batch_update_patches_with_converted_amounts(self, mock_ctx, mocker):
        """Converts amounts and PATCHes with {transactions: [...]}."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "transaction_ids": ["txn-001"],
            "duplicate_import_ids": [],
            "transactions": [],
        }

        await batch_update_transactions(
            mock_ctx,
            transactions=[
                {"id": "txn-001", "amount": -30.00},
            ],
        )

        call_args = mock_ctx.lifespan_context.client.patch.call_args
        assert "/budgets/budget-123/transactions" in call_args[0][0]
        txns = call_args[1]["json"]["transactions"]
        assert txns[0]["amount"] == -30000

    @pytest.mark.anyio
    async def test_batch_update_returns_summary(self, mock_ctx, mocker):
        """Returns summary count and per-transaction ID lines."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "transaction_ids": ["txn-001", "txn-002"],
            "duplicate_import_ids": [],
            "transactions": [],
        }

        result = await batch_update_transactions(
            mock_ctx,
            transactions=[
                {"id": "txn-001", "memo": "Updated"},
                {"id": "txn-002", "memo": "Also updated"},
            ],
        )

        assert "2" in result
        assert "updated" in result.lower()
        assert "txn-001" in result
        assert "txn-002" in result

    @pytest.mark.anyio
    async def test_batch_update_empty_raises(self, mock_ctx, mocker):
        """Empty batch raises ToolError."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError):
            await batch_update_transactions(mock_ctx, transactions=[])


class TestImportTransactions:
    """Tests for import_transactions tool."""

    @pytest.mark.anyio
    async def test_import_posts_and_returns_ids(self, mock_ctx, mocker):
        """POSTs to /transactions/import and returns count + IDs."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction_ids": ["txn-import-001", "txn-import-002"],
        }

        result = await import_transactions(mock_ctx)

        call_args = mock_ctx.lifespan_context.client.post.call_args
        assert "/transactions/import" in call_args[0][0]
        assert "2" in result
        assert "imported" in result.lower()
        assert "txn-import-001" in result
        assert "txn-import-002" in result

    @pytest.mark.anyio
    async def test_import_empty_result(self, mock_ctx, mocker):
        """Empty import returns 'No transactions to import.'."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "transaction_ids": [],
        }

        result = await import_transactions(mock_ctx)

        assert "No transactions to import." in result
