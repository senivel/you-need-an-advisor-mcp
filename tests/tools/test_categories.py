"""Tests for manage_categories consolidated tool."""

import pytest
from fastmcp.exceptions import ToolError

from ynaa_mcp.tools.categories import manage_categories


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


class TestManageCategoriesList:
    """Tests for manage_categories(action='list')."""

    @pytest.mark.anyio
    async def test_list_categories(self, mock_ctx, mocker):
        """Hierarchy format with count header and indentation."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_category_groups()

        result = await manage_categories(mock_ctx, action="list")

        assert "2 categories found:" in result
        assert "Fixed Expenses" in result
        assert "Flexible Spending" in result
        assert "  - Rent" in result
        assert "  - Groceries" in result
        assert "$1,500.00" in result
        assert "$500.00" in result
        assert "ID: group-1" in result
        assert "ID: group-2" in result
        assert "ID: cat-1" in result
        assert "ID: cat-3" in result

    @pytest.mark.anyio
    async def test_list_categories_filters_hidden(self, mock_ctx, mocker):
        """Hidden categories excluded by default."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_category_groups()

        result = await manage_categories(mock_ctx, action="list")

        assert "Utilities" not in result

    @pytest.mark.anyio
    async def test_list_categories_include_hidden(self, mock_ctx, mocker):
        """include_hidden=True shows all categories."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_category_groups()

        result = await manage_categories(mock_ctx, action="list", include_hidden=True)

        assert "Utilities" in result
        assert "3 categories found:" in result

    @pytest.mark.anyio
    async def test_list_categories_filters_deleted(self, mock_ctx, mocker):
        """Deleted groups and categories always excluded."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_category_groups()

        result = await manage_categories(mock_ctx, action="list")

        assert "Old Group" not in result
        assert "Old Category" not in result

    @pytest.mark.anyio
    async def test_list_categories_empty(self, mock_ctx, mocker):
        """Empty budget returns appropriate message."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = {"category_groups": []}

        result = await manage_categories(mock_ctx, action="list")

        assert result == "No categories found."


class TestManageCategoriesGet:
    """Tests for manage_categories(action='get')."""

    @pytest.mark.anyio
    async def test_get_category(self, mock_ctx, mocker):
        """Detail view with all fields."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
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

        result = await manage_categories(mock_ctx, action="get", category_id="cat-1")

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
            "ynaa_mcp.tools.categories.resolve_budget",
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

        result = await manage_categories(mock_ctx, action="get", category_id="cat-3")

        assert "Goal" in result
        assert "Needed for Spending" in result
        assert "100%" in result

    @pytest.mark.anyio
    async def test_get_category_without_goal(self, mock_ctx, mocker):
        """No goal section when goal_type is None."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
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

        result = await manage_categories(mock_ctx, action="get", category_id="cat-1")

        assert "Goal" not in result

    @pytest.mark.anyio
    async def test_get_category_missing_id_raises(self, mock_ctx, mocker):
        """ToolError raised when category_id missing for get action."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="category_id is required"):
            await manage_categories(mock_ctx, action="get")


class TestManageCategoriesCreate:
    """Tests for manage_categories(action='create')."""

    @pytest.mark.anyio
    async def test_create_category(self, mock_ctx, mocker):
        """POST body correct, confirmation format."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "category": {
                "id": "new-cat-1",
                "name": "Subscriptions",
                "category_group_id": "group-1",
                "budgeted": 0.0,
                "activity": 0.0,
                "balance": 0.0,
            }
        }

        result = await manage_categories(
            mock_ctx,
            action="create",
            name="Subscriptions",
            category_group_id="group-1",
        )

        assert "Category created" in result
        assert "Subscriptions" in result
        mock_ctx.lifespan_context.client.post.assert_called_once()
        call_args = mock_ctx.lifespan_context.client.post.call_args
        assert call_args[0][0] == "/budgets/budget-123/categories"
        body = call_args[1]["json"]
        assert body["category"]["name"] == "Subscriptions"
        assert body["category"]["category_group_id"] == "group-1"

    @pytest.mark.anyio
    async def test_create_category_with_goal(self, mock_ctx, mocker):
        """goal_target converted to milliunits in POST body."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "category": {
                "id": "new-cat-2",
                "name": "Savings",
                "budgeted": 0.0,
                "activity": 0.0,
                "balance": 0.0,
            }
        }

        result = await manage_categories(
            mock_ctx, action="create", name="Savings", goal_target=500.0
        )

        assert "Category created" in result
        call_args = mock_ctx.lifespan_context.client.post.call_args
        body = call_args[1]["json"]
        assert body["category"]["goal_target"] == 500000


class TestManageCategoriesUpdate:
    """Tests for manage_categories(action='update')."""

    @pytest.mark.anyio
    async def test_update_category(self, mock_ctx, mocker):
        """PATCH body only includes provided fields, category_id in path."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "category": {
                "id": "cat-1",
                "name": "Rent Updated",
                "budgeted": 1500.0,
                "activity": -1500.0,
                "balance": 0.0,
            }
        }

        result = await manage_categories(
            mock_ctx, action="update", name="Rent Updated", category_id="cat-1"
        )

        assert "Category updated" in result
        assert "Rent Updated" in result
        call_args = mock_ctx.lifespan_context.client.patch.call_args
        assert call_args[0][0] == "/budgets/budget-123/categories/cat-1"
        body = call_args[1]["json"]
        assert body["category"]["name"] == "Rent Updated"
        assert "note" not in body["category"]
        assert "goal_target" not in body["category"]

    @pytest.mark.anyio
    async def test_update_category_goal_conversion(self, mock_ctx, mocker):
        """goal_target converted from dollars to milliunits in PATCH."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "category": {
                "id": "cat-1",
                "name": "Savings",
                "budgeted": 0.0,
                "activity": 0.0,
                "balance": 0.0,
            }
        }

        await manage_categories(
            mock_ctx,
            action="update",
            category_id="cat-1",
            name="Savings",
            goal_target=250.50,
        )

        call_args = mock_ctx.lifespan_context.client.patch.call_args
        body = call_args[1]["json"]
        assert body["category"]["goal_target"] == 250500


class TestManageCategoriesGroup:
    """Tests for manage_categories(action='create_group'|'update_group')."""

    @pytest.mark.anyio
    async def test_create_group(self, mock_ctx, mocker):
        """POST body correct, confirmation format."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.post.return_value = {
            "category_group": {
                "id": "new-group-1",
                "name": "Investments",
            }
        }

        result = await manage_categories(
            mock_ctx, action="create_group", name="Investments"
        )

        assert "Category group created" in result
        assert "Investments" in result
        call_args = mock_ctx.lifespan_context.client.post.call_args
        assert call_args[0][0] == "/budgets/budget-123/category_groups"
        body = call_args[1]["json"]
        assert body["category_group"]["name"] == "Investments"

    @pytest.mark.anyio
    async def test_create_group_name_too_long(self, mock_ctx, mocker):
        """ToolError raised for name > 50 chars."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )

        with pytest.raises(ToolError, match="50 characters"):
            await manage_categories(mock_ctx, action="create_group", name="A" * 51)

    @pytest.mark.anyio
    async def test_update_group(self, mock_ctx, mocker):
        """PATCH body correct, confirmation, category_group_id in path."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "category_group": {
                "id": "group-1",
                "name": "Fixed Costs",
            }
        }

        result = await manage_categories(
            mock_ctx,
            action="update_group",
            name="Fixed Costs",
            category_group_id="group-1",
        )

        assert "Category group updated" in result
        assert "Fixed Costs" in result
        call_args = mock_ctx.lifespan_context.client.patch.call_args
        assert call_args[0][0] == "/budgets/budget-123/category_groups/group-1"


def _sample_month_category():
    """Return sample month category data."""
    return {
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
            "note": None,
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


class TestManageCategoriesSetMonthBudget:
    """Tests for manage_categories(action='set_month_budget')."""

    @pytest.mark.anyio
    async def test_get_month_budget(self, mock_ctx, mocker):
        """Correct API path with normalized month, structured output."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_month_category()

        result = await manage_categories(
            mock_ctx,
            action="set_month_budget",
            category_id="cat-1",
            month="2026-03-01",
        )

        assert "Rent" in result
        assert "$1,500.00" in result
        assert "-$1,500.00" in result
        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert (
            call_args[0][0] == "/budgets/budget-123/months/2026-03-01/categories/cat-1"
        )

    @pytest.mark.anyio
    async def test_get_month_budget_default_month(self, mock_ctx, mocker):
        """None month sends 'current' to API."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_month_category()

        await manage_categories(
            mock_ctx, action="set_month_budget", category_id="cat-1"
        )

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert "/months/current/" in call_args[0][0]

    @pytest.mark.anyio
    async def test_get_month_budget_normalizes(self, mock_ctx, mocker):
        """'2026-03' becomes '2026-03-01' in API path."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.get.return_value = _sample_month_category()

        await manage_categories(
            mock_ctx,
            action="set_month_budget",
            category_id="cat-1",
            month="2026-03",
        )

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert "/months/2026-03-01/" in call_args[0][0]

    @pytest.mark.anyio
    async def test_set_month_budget(self, mock_ctx, mocker):
        """Budgeted converted to milliunits, correct PATCH body."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "category": {
                "id": "cat-1",
                "name": "Rent",
                "budgeted": 1600.0,
            }
        }

        result = await manage_categories(
            mock_ctx,
            action="set_month_budget",
            category_id="cat-1",
            month="2026-03",
            budgeted=1600.0,
        )

        assert "Category budget updated" in result
        call_args = mock_ctx.lifespan_context.client.patch.call_args
        assert (
            call_args[0][0] == "/budgets/budget-123/months/2026-03-01/categories/cat-1"
        )
        body = call_args[1]["json"]
        assert body["category"]["budgeted"] == 1600000

    @pytest.mark.anyio
    async def test_set_month_budget_default_month(self, mock_ctx, mocker):
        """None month defaults to 'current' for update."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "category": {
                "id": "cat-1",
                "name": "Rent",
                "budgeted": 1500.0,
            }
        }

        await manage_categories(
            mock_ctx,
            action="set_month_budget",
            category_id="cat-1",
            budgeted=1500.0,
        )

        call_args = mock_ctx.lifespan_context.client.patch.call_args
        assert "/months/current/" in call_args[0][0]

    @pytest.mark.anyio
    async def test_set_month_budget_confirmation(self, mock_ctx, mocker):
        """Response includes formatted dollar amount."""
        mocker.patch(
            "ynaa_mcp.tools.categories.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "category": {
                "id": "cat-1",
                "name": "Rent",
                "budgeted": 1600.0,
            }
        }

        result = await manage_categories(
            mock_ctx,
            action="set_month_budget",
            category_id="cat-1",
            month="2026-03",
            budgeted=1600.0,
        )

        assert "$1,600.00" in result
        assert "Rent" in result
