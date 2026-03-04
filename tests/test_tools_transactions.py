"""Tests for transaction tools: list_transactions, get_transaction."""

import pytest
from fastmcp.exceptions import ToolError

from ynab_mcp.server import list_transactions


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
