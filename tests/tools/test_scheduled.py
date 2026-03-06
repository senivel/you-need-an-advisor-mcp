"""Tests for scheduled transaction tools: list, get, manage, delete."""

import pytest
from fastmcp.exceptions import ToolError

from ynab_mcp.tools.scheduled import (
    delete_scheduled_transaction,
    get_scheduled_transaction,
    list_scheduled_transactions,
    manage_scheduled_transaction,
)


def _make_scheduled_transaction(  # noqa: PLR0913
    *,
    st_id="st-001",
    date_first="2026-01-15",
    date_next="2026-04-15",
    frequency="monthly",
    amount=-100.00,
    payee_name="Electric Company",
    payee_id="payee-111",
    category_name="Utilities",
    category_id="cat-111",
    account_name="Checking",
    account_id="acct-111",
    memo=None,
    flag_color=None,
    flag_name=None,
    transfer_account_id=None,
    subtransactions=None,
    deleted=False,
):
    """Build a sample scheduled transaction dict matching YNAB API shape.

    Returns:
        Dict with scheduled transaction fields.
    """
    return {
        "id": st_id,
        "date_first": date_first,
        "date_next": date_next,
        "frequency": frequency,
        "amount": amount,
        "payee_name": payee_name,
        "payee_id": payee_id,
        "category_name": category_name,
        "category_id": category_id,
        "account_name": account_name,
        "account_id": account_id,
        "memo": memo,
        "flag_color": flag_color,
        "flag_name": flag_name,
        "transfer_account_id": transfer_account_id,
        "subtransactions": subtransactions or [],
        "deleted": deleted,
    }


class TestListScheduledTransactions:
    """Tests for list_scheduled_transactions tool."""

    @pytest.mark.anyio
    async def test_list_returns_count_and_formatted_lines(self, mock_ctx, mocker):
        """Count header with date_next|payee|amount|category [frequency]."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "scheduled_transactions": [
                _make_scheduled_transaction(
                    st_id="st-001",
                    date_next="2026-04-15",
                    payee_name="Electric Company",
                    amount=-100.00,
                    category_name="Utilities",
                    frequency="monthly",
                ),
                _make_scheduled_transaction(
                    st_id="st-002",
                    date_next="2026-04-01",
                    payee_name="Landlord",
                    amount=-1500.00,
                    category_name="Rent",
                    frequency="monthly",
                ),
            ],
        }

        result = await list_scheduled_transactions(mock_ctx)

        assert "2 scheduled transactions found:" in result
        assert "2026-04-15" in result
        assert "Electric Company" in result
        assert "-$100.00" in result
        assert "Utilities" in result
        assert "[monthly]" in result
        assert "ID: st-001" in result
        assert "Landlord" in result
        assert "ID: st-002" in result

    @pytest.mark.anyio
    async def test_list_excludes_deleted(self, mock_ctx, mocker):
        """Deleted scheduled transactions are excluded from listing."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "scheduled_transactions": [
                _make_scheduled_transaction(st_id="st-001", deleted=False),
                _make_scheduled_transaction(st_id="st-002", deleted=True),
            ],
        }

        result = await list_scheduled_transactions(mock_ctx)

        assert "1 scheduled transaction found:" in result
        assert "st-001" in result
        assert "st-002" not in result

    @pytest.mark.anyio
    async def test_list_uses_date_first_when_no_date_next(self, mock_ctx, mocker):
        """Falls back to date_first when date_next is None."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "scheduled_transactions": [
                _make_scheduled_transaction(
                    st_id="st-001",
                    date_first="2026-01-15",
                    date_next=None,
                ),
            ],
        }

        result = await list_scheduled_transactions(mock_ctx)

        assert "2026-01-15" in result

    @pytest.mark.anyio
    async def test_list_empty(self, mock_ctx, mocker):
        """Empty result returns appropriate message."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "scheduled_transactions": [],
        }

        result = await list_scheduled_transactions(mock_ctx)

        assert result == "No scheduled transactions found."


class TestGetScheduledTransaction:
    """Tests for get_scheduled_transaction tool."""

    @pytest.mark.anyio
    async def test_full_detail(self, mock_ctx, mocker):
        """Returns full detail with frequency, first date, next date."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "scheduled_transaction": _make_scheduled_transaction(
                st_id="st-001",
                date_first="2026-01-15",
                date_next="2026-04-15",
                frequency="monthly",
                payee_name="Electric Company",
                amount=-100.00,
                category_name="Utilities",
                account_name="Checking",
                memo="Monthly bill",
                flag_color="blue",
            ),
        }

        result = await get_scheduled_transaction(
            mock_ctx, scheduled_transaction_id="st-001"
        )

        assert "Scheduled: Electric Company" in result
        assert "ID: st-001" in result
        assert "-$100.00" in result
        assert "Account: Checking" in result
        assert "Category: Utilities" in result
        assert "Frequency: monthly" in result
        assert "First date: 2026-01-15" in result
        assert "Next date: 2026-04-15" in result
        assert "Memo: Monthly bill" in result
        assert "Flag: blue" in result

    @pytest.mark.anyio
    async def test_subtransactions(self, mock_ctx, mocker):
        """Shows subtransactions as indented list."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "scheduled_transaction": _make_scheduled_transaction(
                subtransactions=[
                    {
                        "amount": -60.00,
                        "category_name": "Utilities",
                        "memo": "Electric",
                    },
                    {
                        "amount": -40.00,
                        "category_name": "Utilities",
                        "memo": None,
                    },
                ],
            ),
        }

        result = await get_scheduled_transaction(
            mock_ctx, scheduled_transaction_id="st-001"
        )

        assert "Split (2 items):" in result
        assert "-$60.00 | Utilities" in result
        assert "Memo: Electric" in result
        assert "-$40.00 | Utilities" in result

    @pytest.mark.anyio
    async def test_no_date_next(self, mock_ctx, mocker):
        """Omits next date line when date_next is None."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "scheduled_transaction": _make_scheduled_transaction(
                date_next=None,
            ),
        }

        result = await get_scheduled_transaction(
            mock_ctx, scheduled_transaction_id="st-001"
        )

        assert "Next date:" not in result


class TestManageScheduledTransaction:
    """Tests for manage_scheduled_transaction tool (create/update)."""

    @pytest.mark.anyio
    async def test_create_sends_post(self, mock_ctx, mocker):
        """Create mode (no scheduled_transaction_id) POSTs with required fields."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "scheduled_transaction": _make_scheduled_transaction(
                st_id="st-new",
                date_first="2026-04-01",
                payee_name="Landlord",
                amount=-1500.00,
                account_name="Checking",
                frequency="monthly",
            ),
        }

        result = await manage_scheduled_transaction(
            mock_ctx,
            budget_id_or_name="budget-123",
            account_id="acct-111",
            date="2026-04-01",
            amount=-1500.00,
            frequency="monthly",
            payee_name="Landlord",
        )

        call_args = mock_ctx.lifespan_context.client.post.call_args
        assert "/budgets/budget-123/scheduled_transactions" in call_args[0][0]
        body = call_args[1]["json"]["scheduled_transaction"]
        assert body["account_id"] == "acct-111"
        assert body["date"] == "2026-04-01"
        assert body["amount"] == -1500000
        assert body["frequency"] == "monthly"
        assert "created" in result.lower()

    @pytest.mark.anyio
    async def test_create_missing_required_raises(self, mock_ctx, mocker):
        """Create mode missing account_id or date raises ToolError."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="account_id"):
            await manage_scheduled_transaction(
                mock_ctx,
                budget_id_or_name="budget-123",
                date="2026-04-01",
                amount=-100.00,
            )

    @pytest.mark.anyio
    async def test_update_sends_put(self, mock_ctx, mocker):
        """Update mode (with scheduled_transaction_id) sends PUT."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.put.return_value = {
            "scheduled_transaction": _make_scheduled_transaction(
                st_id="st-001",
                memo="Updated memo",
            ),
        }

        result = await manage_scheduled_transaction(
            mock_ctx,
            budget_id_or_name="budget-123",
            scheduled_transaction_id="st-001",
            memo="Updated memo",
        )

        call_args = mock_ctx.lifespan_context.client.put.call_args
        assert "/scheduled_transactions/st-001" in call_args[0][0]
        body = call_args[1]["json"]["scheduled_transaction"]
        assert body["memo"] == "Updated memo"
        assert "updated" in result.lower()

    @pytest.mark.anyio
    async def test_create_returns_confirmation(self, mock_ctx, mocker):
        """Create returns confirmation with payee, amount, frequency."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "scheduled_transaction": _make_scheduled_transaction(
                st_id="st-new",
                payee_name="Landlord",
                amount=-1500.00,
                account_name="Checking",
                frequency="monthly",
            ),
        }

        result = await manage_scheduled_transaction(
            mock_ctx,
            budget_id_or_name="budget-123",
            account_id="acct-111",
            date="2026-04-01",
            amount=-1500.00,
            frequency="monthly",
            payee_name="Landlord",
        )

        assert "Landlord" in result
        assert "-$1,500.00" in result
        assert "monthly" in result


class TestDeleteScheduledTransaction:
    """Tests for delete_scheduled_transaction tool."""

    @pytest.mark.anyio
    async def test_delete_sends_delete(self, mock_ctx, mocker):
        """delete_scheduled_transaction sends DELETE and returns confirmation."""
        mocker.patch(
            "ynab_mcp.tools.scheduled.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.delete.return_value = {
            "scheduled_transaction": _make_scheduled_transaction(
                st_id="st-001",
                payee_name="Electric Company",
                amount=-100.00,
                frequency="monthly",
            ),
        }

        result = await delete_scheduled_transaction(
            mock_ctx, scheduled_transaction_id="st-001"
        )

        call_args = mock_ctx.lifespan_context.client.delete.call_args
        assert "/scheduled_transactions/st-001" in call_args[0][0]
        assert "deleted" in result.lower()
        assert "Electric Company" in result
        assert "-$100.00" in result
