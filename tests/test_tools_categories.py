"""Tests for category tools: get_categories, get_category."""

import pytest

from ynab_mcp.server import get_categories, get_category


@pytest.fixture
def mock_ctx(mocker):
    """Create a mock MCP Context with a mocked YNABClient."""
    client = mocker.AsyncMock()
    app = mocker.MagicMock()
    app.client = client
    ctx = mocker.MagicMock()
    ctx.lifespan_context = app
    return ctx


def _sample_category_groups():
    """Return sample category group data as returned by YNAB API (post-conversion)."""
    return {
        "category_groups": [
            {
                "id": "group-1",
                "name": "Fixed Expenses",
                "hidden": False,
                "deleted": False,
                "categories": [
                    {
                        "id": "cat-1",
                        "category_group_id": "group-1",
                        "category_group_name": "Fixed Expenses",
                        "name": "Rent",
                        "hidden": False,
                        "budgeted": 1500.0,
                        "activity": -1500.0,
                        "balance": 0.0,
                        "deleted": False,
                        "note": None,
                        "goal_type": None,
                        "goal_target": None,
                        "goal_target_month": None,
                        "goal_percentage_complete": None,
                        "goal_months_to_budget": None,
                        "goal_under_funded": None,
                        "goal_overall_funded": None,
                        "goal_overall_left": None,
                    },
                    {
                        "id": "cat-2",
                        "category_group_id": "group-1",
                        "category_group_name": "Fixed Expenses",
                        "name": "Utilities",
                        "hidden": True,
                        "budgeted": 200.0,
                        "activity": -150.0,
                        "balance": 50.0,
                        "deleted": False,
                        "note": None,
                        "goal_type": None,
                        "goal_target": None,
                        "goal_target_month": None,
                        "goal_percentage_complete": None,
                        "goal_months_to_budget": None,
                        "goal_under_funded": None,
                        "goal_overall_funded": None,
                        "goal_overall_left": None,
                    },
                ],
            },
            {
                "id": "group-2",
                "name": "Flexible Spending",
                "hidden": False,
                "deleted": False,
                "categories": [
                    {
                        "id": "cat-3",
                        "category_group_id": "group-2",
                        "category_group_name": "Flexible Spending",
                        "name": "Groceries",
                        "hidden": False,
                        "budgeted": 500.0,
                        "activity": -300.0,
                        "balance": 200.0,
                        "deleted": False,
                        "note": "Weekly shopping",
                        "goal_type": "NEED",
                        "goal_target": 500.0,
                        "goal_target_month": None,
                        "goal_percentage_complete": 100,
                        "goal_months_to_budget": None,
                        "goal_under_funded": 0.0,
                        "goal_overall_funded": None,
                        "goal_overall_left": None,
                    },
                ],
            },
            {
                "id": "group-deleted",
                "name": "Old Group",
                "hidden": False,
                "deleted": True,
                "categories": [
                    {
                        "id": "cat-deleted",
                        "category_group_id": "group-deleted",
                        "name": "Old Category",
                        "hidden": False,
                        "budgeted": 0.0,
                        "activity": 0.0,
                        "balance": 0.0,
                        "deleted": True,
                    },
                ],
            },
        ]
    }


class TestGetCategories:
    """Tests for get_categories tool."""

    @pytest.mark.anyio
    async def test_list_categories(self, mock_ctx, mocker):
        """Hierarchy format with count header and indentation."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_category_groups()

        result = await get_categories(mock_ctx)

        # Count header (2 visible: Rent + Groceries, hidden Utilities excluded)
        assert "2 categories found:" in result
        # Group headers
        assert "Fixed Expenses" in result
        assert "Flexible Spending" in result
        # Category names indented
        assert "  - Rent" in result
        assert "  - Groceries" in result
        # Dollar formatting
        assert "$1,500.00" in result
        assert "$500.00" in result

    @pytest.mark.anyio
    async def test_list_categories_filters_hidden(self, mock_ctx, mocker):
        """Hidden categories excluded by default."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_category_groups()

        result = await get_categories(mock_ctx)

        assert "Utilities" not in result

    @pytest.mark.anyio
    async def test_list_categories_include_hidden(self, mock_ctx, mocker):
        """include_hidden=True shows all categories."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_category_groups()

        result = await get_categories(mock_ctx, include_hidden=True)

        assert "Utilities" in result
        assert "3 categories found:" in result

    @pytest.mark.anyio
    async def test_list_categories_filters_deleted(self, mock_ctx, mocker):
        """Deleted groups and categories always excluded."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_category_groups()

        result = await get_categories(mock_ctx)

        assert "Old Group" not in result
        assert "Old Category" not in result

    @pytest.mark.anyio
    async def test_list_categories_empty(self, mock_ctx, mocker):
        """Empty budget returns appropriate message."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {"category_groups": []}

        result = await get_categories(mock_ctx)

        assert result == "No categories found."


class TestGetCategory:
    """Tests for get_category tool."""

    @pytest.mark.anyio
    async def test_get_category(self, mock_ctx, mocker):
        """Detail view with all fields."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "category": {
                "id": "cat-1",
                "category_group_id": "group-1",
                "category_group_name": "Fixed Expenses",
                "name": "Rent",
                "hidden": False,
                "budgeted": 1500.0,
                "activity": -1500.0,
                "balance": 0.0,
                "deleted": False,
                "note": "Monthly rent payment",
                "goal_type": None,
                "goal_target": None,
                "goal_target_month": None,
                "goal_percentage_complete": None,
                "goal_months_to_budget": None,
                "goal_under_funded": None,
                "goal_overall_funded": None,
                "goal_overall_left": None,
            }
        }

        result = await get_category(mock_ctx, category_id="cat-1")

        assert "Rent" in result
        assert "Fixed Expenses" in result
        assert "$1,500.00" in result
        assert "-$1,500.00" in result
        assert "$0.00" in result
        assert "Monthly rent payment" in result

    @pytest.mark.anyio
    async def test_get_category_with_goal(self, mock_ctx, mocker):
        """Goal section present when goal_type is set."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "category": {
                "id": "cat-3",
                "category_group_id": "group-2",
                "category_group_name": "Flexible Spending",
                "name": "Groceries",
                "hidden": False,
                "budgeted": 500.0,
                "activity": -300.0,
                "balance": 200.0,
                "deleted": False,
                "note": None,
                "goal_type": "NEED",
                "goal_target": 500.0,
                "goal_target_month": None,
                "goal_percentage_complete": 100,
                "goal_months_to_budget": None,
                "goal_under_funded": 0.0,
                "goal_overall_funded": None,
                "goal_overall_left": None,
            }
        }

        result = await get_category(mock_ctx, category_id="cat-3")

        assert "Goal" in result
        assert "Needed for Spending" in result
        assert "100%" in result

    @pytest.mark.anyio
    async def test_get_category_without_goal(self, mock_ctx, mocker):
        """No goal section when goal_type is None."""
        mocker.patch(
            "ynab_mcp.server.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "category": {
                "id": "cat-1",
                "category_group_id": "group-1",
                "name": "Rent",
                "hidden": False,
                "budgeted": 1500.0,
                "activity": -1500.0,
                "balance": 0.0,
                "deleted": False,
                "goal_type": None,
                "goal_target": None,
                "goal_target_month": None,
                "goal_percentage_complete": None,
                "goal_months_to_budget": None,
                "goal_under_funded": None,
                "goal_overall_funded": None,
                "goal_overall_left": None,
            }
        }

        result = await get_category(mock_ctx, category_id="cat-1")

        assert "Goal" not in result
