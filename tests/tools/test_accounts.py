"""Tests for manage_accounts consolidated tool."""

import pytest
from fastmcp.exceptions import ToolError

from ynaa_mcp.tools.accounts import manage_accounts


def _make_account(  # noqa: PLR0913
    *,
    name="Checking",
    account_type="checking",
    balance=1500.0,
    cleared_balance=1400.0,
    uncleared_balance=100.0,
    on_budget=True,
    closed=False,
    deleted=False,
    note=None,
    account_id="acct-111",
    transfer_payee_id=None,
):
    """Build a sample account dict matching YNAB API shape (post-conversion).

    Returns:
        Dict with account fields.
    """
    return {
        "id": account_id,
        "name": name,
        "type": account_type,
        "on_budget": on_budget,
        "closed": closed,
        "balance": balance,
        "cleared_balance": cleared_balance,
        "uncleared_balance": uncleared_balance,
        "note": note,
        "transfer_payee_id": transfer_payee_id,
        "deleted": deleted,
    }


class TestManageAccountsList:
    """Tests for manage_accounts(action='list')."""

    @pytest.mark.anyio
    async def test_list_accounts(self, mock_ctx, mocker):
        """Count header, structured format, dollar formatting."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [
                _make_account(name="Checking", balance=1500.0),
                _make_account(
                    name="Savings",
                    account_type="savings",
                    balance=25000.50,
                    account_id="acct-222",
                ),
            ],
        }

        result = await manage_accounts(mock_ctx, action="list")

        assert "2 accounts found:" in result
        assert "Checking" in result
        assert "Type: checking" in result
        assert "$1,500.00" in result
        assert "Savings" in result
        assert "$25,000.50" in result
        assert "ID: acct-111" in result
        assert "ID: acct-222" in result

    @pytest.mark.anyio
    async def test_list_accounts_excludes_closed(self, mock_ctx, mocker):
        """Closed accounts filtered by default."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [
                _make_account(name="Open Account"),
                _make_account(name="Closed Account", closed=True),
                _make_account(name="Deleted Account", deleted=True),
            ],
        }

        result = await manage_accounts(mock_ctx, action="list")

        assert "1 account found:" in result
        assert "Open Account" in result
        assert "Closed Account" not in result
        assert "Deleted Account" not in result

    @pytest.mark.anyio
    async def test_list_accounts_include_closed(self, mock_ctx, mocker):
        """include_closed=True shows closed but not deleted accounts."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [
                _make_account(name="Open Account"),
                _make_account(name="Closed Account", closed=True),
                _make_account(name="Deleted Account", deleted=True),
            ],
        }

        result = await manage_accounts(mock_ctx, action="list", include_closed=True)

        assert "2 accounts found:" in result
        assert "Open Account" in result
        assert "Closed Account" in result
        assert "Deleted Account" not in result

    @pytest.mark.anyio
    async def test_list_accounts_empty(self, mock_ctx, mocker):
        """No accounts returns appropriate message."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [],
        }

        result = await manage_accounts(mock_ctx, action="list")

        assert result == "No accounts found."

    @pytest.mark.anyio
    async def test_list_accounts_empty_after_filter(self, mock_ctx, mocker):
        """All accounts closed returns filtered message."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [
                _make_account(name="Closed Account", closed=True),
            ],
        }

        result = await manage_accounts(mock_ctx, action="list")

        assert result == "No open accounts found."

    @pytest.mark.anyio
    async def test_list_accounts_prepends_info(self, mock_ctx, mocker):
        """Info message from resolve_budget is prepended."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", "Using budget 'My Budget' (only budget found)"),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [
                _make_account(name="Checking"),
            ],
        }

        result = await manage_accounts(mock_ctx, action="list")

        assert result.startswith("Using budget 'My Budget' (only budget found)")


class TestManageAccountsGet:
    """Tests for manage_accounts(action='get')."""

    @pytest.mark.anyio
    async def test_get_account(self, mock_ctx, mocker):
        """Detail view has all fields, dollar amounts formatted."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "account": _make_account(
                name="Checking",
                balance=1500.0,
                cleared_balance=1400.0,
                uncleared_balance=100.0,
                note="Primary checking",
                on_budget=True,
                closed=False,
            ),
        }

        result = await manage_accounts(mock_ctx, action="get", account_id="acct-111")

        assert "Checking" in result
        assert "Type: checking" in result
        assert "On budget: Yes" in result
        assert "$1,500.00" in result
        assert "$1,400.00" in result
        assert "$100.00" in result
        assert "Primary checking" in result
        assert "Closed: No" in result

    @pytest.mark.anyio
    async def test_get_account_no_note(self, mock_ctx, mocker):
        """Note line omitted when note is None."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "account": _make_account(note=None),
        }

        result = await manage_accounts(mock_ctx, action="get", account_id="acct-111")

        assert "Note:" not in result

    @pytest.mark.anyio
    async def test_get_account_prepends_info(self, mock_ctx, mocker):
        """Info message from resolve_budget is prepended."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", "Using budget 'My Budget' (only budget found)"),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "account": _make_account(),
        }

        result = await manage_accounts(mock_ctx, action="get", account_id="acct-111")

        assert result.startswith("Using budget 'My Budget' (only budget found)")

    @pytest.mark.anyio
    async def test_get_account_missing_id_raises(self, mock_ctx, mocker):
        """ToolError raised when account_id is missing for get action."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="account_id is required"):
            await manage_accounts(mock_ctx, action="get")


class TestManageAccountsCreate:
    """Tests for manage_accounts(action='create')."""

    @pytest.mark.anyio
    async def test_create_account(self, mock_ctx, mocker):
        """Verifies POST called with milliunits, confirmation message format."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "account": _make_account(
                name="New Savings",
                account_type="savings",
                balance=500.0,
                account_id="acct-new-999",
            ),
        }

        result = await manage_accounts(
            mock_ctx,
            action="create",
            name="New Savings",
            account_type="savings",
            balance=500.0,
        )

        assert "Account created:" in result
        assert "New Savings" in result
        assert "Type: savings" in result
        assert "$500.00" in result
        assert "acct-new-999" in result

        # Verify POST was called with correct path and body
        mock_ctx.lifespan_context.client.post.assert_called_once_with(
            "/budgets/budget-123/accounts",
            json={
                "account": {
                    "name": "New Savings",
                    "type": "savings",
                    "balance": 500000,
                }
            },
        )

    @pytest.mark.anyio
    async def test_create_account_dollar_conversion(self, mock_ctx, mocker):
        """$100.50 -> 100500 milliunits in request body."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "account": _make_account(
                name="Checking",
                account_type="checking",
                balance=100.50,
                account_id="acct-new-888",
            ),
        }

        await manage_accounts(
            mock_ctx,
            action="create",
            name="Checking",
            account_type="checking",
            balance=100.50,
        )

        call_kwargs = mock_ctx.lifespan_context.client.post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert body["account"]["balance"] == 100500

    @pytest.mark.anyio
    async def test_create_account_prepends_info(self, mock_ctx, mocker):
        """Info message from resolve_budget is prepended."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=(
                "budget-123",
                "Using budget 'My Budget' (only budget found)",
            ),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "account": _make_account(account_id="acct-new-777"),
        }

        result = await manage_accounts(
            mock_ctx,
            action="create",
            name="Checking",
            account_type="checking",
            balance=0.0,
        )

        assert result.startswith("Using budget 'My Budget' (only budget found)")

    @pytest.mark.anyio
    async def test_create_account_missing_params_raises(self, mock_ctx, mocker):
        """ToolError raised when required create params are missing."""
        mocker.patch(
            "ynaa_mcp.tools.accounts.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="name, account_type, and balance"):
            await manage_accounts(mock_ctx, action="create", name="Test")
