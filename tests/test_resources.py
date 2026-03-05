"""Tests for MCP Resources: budget accounts, categories, payees."""

import json

import pytest

from ynab_mcp.resources import budget_accounts, budget_categories, budget_payees


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


class TestBudgetAccounts:
    """Tests for budget_accounts resource."""

    @pytest.mark.anyio
    async def test_budget_accounts_filters_deleted(self, mock_ctx):
        """Deleted accounts are excluded from results."""
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [
                {
                    "id": "acct-1",
                    "name": "Checking",
                    "type": "checking",
                    "on_budget": True,
                    "closed": False,
                    "balance": 1500.0,
                    "deleted": False,
                },
                {
                    "id": "acct-2",
                    "name": "Old Savings",
                    "type": "savings",
                    "on_budget": True,
                    "closed": False,
                    "balance": 0.0,
                    "deleted": True,
                },
                {
                    "id": "acct-3",
                    "name": "Credit Card",
                    "type": "creditCard",
                    "on_budget": True,
                    "closed": False,
                    "balance": -250.0,
                    "deleted": False,
                },
            ],
        }

        result = await budget_accounts("budget-123", mock_ctx)
        data = json.loads(result)

        assert len(data) == 2
        names = [a["name"] for a in data]
        assert "Checking" in names
        assert "Credit Card" in names
        assert "Old Savings" not in names

    @pytest.mark.anyio
    async def test_budget_accounts_includes_balances(self, mock_ctx):
        """Balance field is present in output."""
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [
                {
                    "id": "acct-1",
                    "name": "Checking",
                    "type": "checking",
                    "on_budget": True,
                    "closed": False,
                    "balance": 1500.50,
                    "deleted": False,
                },
            ],
        }

        result = await budget_accounts("budget-123", mock_ctx)
        data = json.loads(result)

        assert data[0]["balance"] == 1500.50

    @pytest.mark.anyio
    async def test_budget_accounts_returns_valid_json(self, mock_ctx):
        """Resource returns parseable JSON."""
        mock_ctx.lifespan_context.client.get.return_value = {
            "accounts": [
                {
                    "id": "acct-1",
                    "name": "Checking",
                    "type": "checking",
                    "on_budget": True,
                    "closed": False,
                    "balance": 100.0,
                    "deleted": False,
                },
            ],
        }

        result = await budget_accounts("budget-123", mock_ctx)
        parsed = json.loads(result)

        assert isinstance(parsed, list)


class TestBudgetCategories:
    """Tests for budget_categories resource."""

    @pytest.mark.anyio
    async def test_budget_categories_filters_deleted_and_hidden(
        self,
        mock_ctx,
    ):
        """Deleted groups, deleted categories, and hidden categories excluded."""
        mock_ctx.lifespan_context.client.get.return_value = {
            "category_groups": [
                {
                    "id": "grp-1",
                    "name": "Bills",
                    "deleted": False,
                    "categories": [
                        {
                            "id": "cat-1",
                            "name": "Rent",
                            "budgeted": 1200.0,
                            "activity": -1200.0,
                            "balance": 0.0,
                            "deleted": False,
                            "hidden": False,
                        },
                        {
                            "id": "cat-2",
                            "name": "Old Bill",
                            "budgeted": 0.0,
                            "activity": 0.0,
                            "balance": 0.0,
                            "deleted": True,
                            "hidden": False,
                        },
                        {
                            "id": "cat-3",
                            "name": "Hidden Bill",
                            "budgeted": 0.0,
                            "activity": 0.0,
                            "balance": 0.0,
                            "deleted": False,
                            "hidden": True,
                        },
                    ],
                },
                {
                    "id": "grp-2",
                    "name": "Deleted Group",
                    "deleted": True,
                    "categories": [
                        {
                            "id": "cat-4",
                            "name": "Whatever",
                            "budgeted": 0.0,
                            "activity": 0.0,
                            "balance": 0.0,
                            "deleted": False,
                            "hidden": False,
                        },
                    ],
                },
            ],
        }

        result = await budget_categories("budget-123", mock_ctx)
        data = json.loads(result)

        assert len(data) == 1
        assert data[0]["group"] == "Bills"
        assert len(data[0]["categories"]) == 1
        assert data[0]["categories"][0]["name"] == "Rent"

    @pytest.mark.anyio
    async def test_budget_categories_skips_empty_groups(self, mock_ctx):
        """Groups with all hidden/deleted categories are excluded."""
        mock_ctx.lifespan_context.client.get.return_value = {
            "category_groups": [
                {
                    "id": "grp-1",
                    "name": "Active Group",
                    "deleted": False,
                    "categories": [
                        {
                            "id": "cat-1",
                            "name": "Groceries",
                            "budgeted": 500.0,
                            "activity": -300.0,
                            "balance": 200.0,
                            "deleted": False,
                            "hidden": False,
                        },
                    ],
                },
                {
                    "id": "grp-2",
                    "name": "Empty Group",
                    "deleted": False,
                    "categories": [
                        {
                            "id": "cat-2",
                            "name": "Hidden Cat",
                            "budgeted": 0.0,
                            "activity": 0.0,
                            "balance": 0.0,
                            "deleted": False,
                            "hidden": True,
                        },
                    ],
                },
            ],
        }

        result = await budget_categories("budget-123", mock_ctx)
        data = json.loads(result)

        assert len(data) == 1
        assert data[0]["group"] == "Active Group"

    @pytest.mark.anyio
    async def test_budget_categories_returns_valid_json(self, mock_ctx):
        """Resource returns parseable JSON."""
        mock_ctx.lifespan_context.client.get.return_value = {
            "category_groups": [
                {
                    "id": "grp-1",
                    "name": "Bills",
                    "deleted": False,
                    "categories": [
                        {
                            "id": "cat-1",
                            "name": "Rent",
                            "budgeted": 1200.0,
                            "activity": -1200.0,
                            "balance": 0.0,
                            "deleted": False,
                            "hidden": False,
                        },
                    ],
                },
            ],
        }

        result = await budget_categories("budget-123", mock_ctx)
        parsed = json.loads(result)

        assert isinstance(parsed, list)


class TestBudgetPayees:
    """Tests for budget_payees resource."""

    @pytest.mark.anyio
    async def test_budget_payees_filters_deleted_and_transfers(
        self,
        mock_ctx,
    ):
        """Deleted payees and transfer payees are excluded."""
        mock_ctx.lifespan_context.client.get.return_value = {
            "payees": [
                {
                    "id": "payee-1",
                    "name": "Grocery Store",
                    "transfer_account_id": None,
                    "deleted": False,
                },
                {
                    "id": "payee-2",
                    "name": "Transfer: Savings",
                    "transfer_account_id": "acct-savings",
                    "deleted": False,
                },
                {
                    "id": "payee-3",
                    "name": "Old Payee",
                    "transfer_account_id": None,
                    "deleted": True,
                },
                {
                    "id": "payee-4",
                    "name": "Coffee Shop",
                    "transfer_account_id": None,
                    "deleted": False,
                },
            ],
        }

        result = await budget_payees("budget-123", mock_ctx)
        data = json.loads(result)

        assert len(data) == 2
        names = [p["name"] for p in data]
        assert "Grocery Store" in names
        assert "Coffee Shop" in names
        assert "Transfer: Savings" not in names
        assert "Old Payee" not in names

    @pytest.mark.anyio
    async def test_budget_payees_returns_valid_json(self, mock_ctx):
        """Resource returns parseable JSON."""
        mock_ctx.lifespan_context.client.get.return_value = {
            "payees": [
                {
                    "id": "payee-1",
                    "name": "Test Payee",
                    "transfer_account_id": None,
                    "deleted": False,
                },
            ],
        }

        result = await budget_payees("budget-123", mock_ctx)
        parsed = json.loads(result)

        assert isinstance(parsed, list)
        assert parsed[0]["id"] == "payee-1"
        assert parsed[0]["name"] == "Test Payee"
