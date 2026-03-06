"""Tests for month and money movement tools (MNTH-01 through MNTH-06)."""

import pytest

from ynab_mcp.tools.months import (
    get_month,
    list_money_movement_groups,
    list_money_movements,
    list_months,
)


def _make_month_summary(  # noqa: PLR0913
    *,
    month="2026-03-01",
    income=5000.0,
    budgeted=4500.0,
    activity=-3200.0,
    to_be_budgeted=500.0,
    age_of_money=45,
    deleted=False,
):
    """Build a sample month summary dict matching YNAB API shape.

    Returns:
        Dict with month summary fields.
    """
    return {
        "month": month,
        "income": income,
        "budgeted": budgeted,
        "activity": activity,
        "to_be_budgeted": to_be_budgeted,
        "age_of_money": age_of_money,
        "deleted": deleted,
    }


def _make_month_detail(  # noqa: PLR0913
    *,
    month="2026-03-01",
    income=5000.0,
    budgeted=4500.0,
    activity=-3200.0,
    to_be_budgeted=500.0,
    age_of_money=45,
    categories=None,
):
    """Build a sample month detail dict matching YNAB API shape.

    Returns:
        Dict with month detail fields including categories.
    """
    if categories is None:
        categories = [
            {
                "id": "cat-001",
                "category_group_id": "grp-001",
                "category_group_name": "Bills",
                "name": "Rent",
                "hidden": False,
                "budgeted": 1500.0,
                "activity": -1500.0,
                "balance": 0.0,
                "deleted": False,
            },
            {
                "id": "cat-002",
                "category_group_id": "grp-001",
                "category_group_name": "Bills",
                "name": "Electric",
                "hidden": False,
                "budgeted": 100.0,
                "activity": -85.0,
                "balance": 15.0,
                "deleted": False,
            },
            {
                "id": "cat-003",
                "category_group_id": "grp-002",
                "category_group_name": "Fun Money",
                "name": "Dining Out",
                "hidden": False,
                "budgeted": 200.0,
                "activity": -150.0,
                "balance": 50.0,
                "deleted": False,
            },
        ]
    return {
        "month": month,
        "income": income,
        "budgeted": budgeted,
        "activity": activity,
        "to_be_budgeted": to_be_budgeted,
        "age_of_money": age_of_money,
        "categories": categories,
    }


def _make_money_movement(
    *,
    category_name="Groceries",
    category_group_name="Everyday Expenses",
    allocation=500.0,
    spent=-350.0,
    income=0.0,
):
    """Build a sample money movement dict matching YNAB API shape.

    Returns:
        Dict with money movement fields.
    """
    return {
        "category_name": category_name,
        "category_group_name": category_group_name,
        "allocation": allocation,
        "spent": spent,
        "income": income,
    }


def _make_money_movement_group(
    *,
    category_group_name="Everyday Expenses",
    allocation=1200.0,
    spent=-800.0,
    income=0.0,
):
    """Build a sample money movement group dict matching YNAB API shape.

    Returns:
        Dict with money movement group fields.
    """
    return {
        "category_group_name": category_group_name,
        "allocation": allocation,
        "spent": spent,
        "income": income,
    }


class TestListMonths:
    """Tests for list_months tool (MNTH-01)."""

    @pytest.mark.anyio
    async def test_returns_months_with_count_header(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        months = [
            _make_month_summary(month="2026-03-01"),
            _make_month_summary(month="2026-02-01", income=4000.0),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {"months": months}

        result = await list_months(mock_ctx)

        assert "2 months found:" in result
        assert "2026-03-01" in result
        assert "2026-02-01" in result
        assert "$5,000.00" in result
        assert "$4,500.00" in result
        assert "45 days" in result

    @pytest.mark.anyio
    async def test_excludes_deleted_months(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        months = [
            _make_month_summary(month="2026-03-01"),
            _make_month_summary(month="2026-01-01", deleted=True),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {"months": months}

        result = await list_months(mock_ctx)

        assert "1 month found:" in result
        assert "2026-03-01" in result
        assert "2026-01-01" not in result

    @pytest.mark.anyio
    async def test_age_of_money_none(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        months = [_make_month_summary(age_of_money=None)]
        mock_ctx.lifespan_context.client.get.return_value = {"months": months}

        result = await list_months(mock_ctx)

        assert "days" not in result

    @pytest.mark.anyio
    async def test_empty_returns_message(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        mock_ctx.lifespan_context.client.get.return_value = {"months": []}

        result = await list_months(mock_ctx)

        assert result == "No months found."


class TestGetMonth:
    """Tests for get_month tool (MNTH-02)."""

    @pytest.mark.anyio
    async def test_returns_month_detail_with_grouped_categories(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        detail = _make_month_detail()
        mock_ctx.lifespan_context.client.get.return_value = {"month": detail}

        result = await get_month(mock_ctx, month="2026-03")

        # Month summary
        assert "$5,000.00" in result
        assert "45 days" in result
        # Categories grouped by group name
        assert "Bills" in result
        assert "Rent" in result
        assert "Electric" in result
        assert "Fun Money" in result
        assert "Dining Out" in result

    @pytest.mark.anyio
    async def test_categories_grouped_by_group_name(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        detail = _make_month_detail()
        mock_ctx.lifespan_context.client.get.return_value = {"month": detail}

        result = await get_month(mock_ctx, month="2026-03")

        # Bills group should appear before its categories
        bills_pos = result.index("Bills")
        rent_pos = result.index("Rent")
        electric_pos = result.index("Electric")
        assert bills_pos < rent_pos
        assert bills_pos < electric_pos

        # Fun Money group should appear before its categories
        fun_pos = result.index("Fun Money")
        dining_pos = result.index("Dining Out")
        assert fun_pos < dining_pos

    @pytest.mark.anyio
    async def test_normalizes_month_param(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        detail = _make_month_detail()
        mock_ctx.lifespan_context.client.get.return_value = {"month": detail}

        await get_month(mock_ctx, month="2026-03")

        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert "2026-03-01" in call_args[0][0]


class TestListMoneyMovements:
    """Tests for list_money_movements tool (MNTH-03, MNTH-04)."""

    @pytest.mark.anyio
    async def test_budget_wide(self, mock_ctx, mocker):
        """MNTH-03: GET /budgets/{id}/money_movements."""
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        movements = [
            _make_money_movement(category_name="Groceries", allocation=500.0),
            _make_money_movement(
                category_name="Gas", category_group_name="Transport", allocation=200.0
            ),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {
            "money_movements": movements,
        }

        result = await list_money_movements(mock_ctx)

        assert "2 money movements found:" in result
        assert "Groceries" in result
        assert "Gas" in result
        assert "$500.00" in result
        # Verify budget-wide endpoint
        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert call_args[0][0] == "/budgets/budget-1/money_movements"

    @pytest.mark.anyio
    async def test_by_month(self, mock_ctx, mocker):
        """MNTH-04: GET /budgets/{id}/months/{month}/money_movements."""
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        movements = [_make_money_movement()]
        mock_ctx.lifespan_context.client.get.return_value = {
            "money_movements": movements,
        }

        result = await list_money_movements(mock_ctx, month="2026-03")

        assert "1 money movement found:" in result
        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert call_args[0][0] == "/budgets/budget-1/months/2026-03-01/money_movements"

    @pytest.mark.anyio
    async def test_empty_returns_message(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "money_movements": [],
        }

        result = await list_money_movements(mock_ctx)

        assert result == "No money movements found."

    @pytest.mark.anyio
    async def test_shows_category_group(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        movements = [
            _make_money_movement(
                category_name="Groceries",
                category_group_name="Everyday Expenses",
            ),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {
            "money_movements": movements,
        }

        result = await list_money_movements(mock_ctx)

        assert "Everyday Expenses" in result


class TestListMoneyMovementGroups:
    """Tests for list_money_movement_groups tool (MNTH-05, MNTH-06)."""

    @pytest.mark.anyio
    async def test_budget_wide(self, mock_ctx, mocker):
        """MNTH-05: GET /budgets/{id}/money_movement_groups."""
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        groups = [
            _make_money_movement_group(category_group_name="Bills", allocation=2000.0),
            _make_money_movement_group(category_group_name="Fun", allocation=500.0),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {
            "money_movement_groups": groups,
        }

        result = await list_money_movement_groups(mock_ctx)

        assert "2 money movement groups found:" in result
        assert "Bills" in result
        assert "Fun" in result
        assert "$2,000.00" in result
        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert call_args[0][0] == "/budgets/budget-1/money_movement_groups"

    @pytest.mark.anyio
    async def test_by_month(self, mock_ctx, mocker):
        """MNTH-06: GET /budgets/{id}/months/{month}/money_movement_groups."""
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        groups = [_make_money_movement_group()]
        mock_ctx.lifespan_context.client.get.return_value = {
            "money_movement_groups": groups,
        }

        result = await list_money_movement_groups(mock_ctx, month="2026-03")

        assert "1 money movement group found:" in result
        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert (
            call_args[0][0]
            == "/budgets/budget-1/months/2026-03-01/money_movement_groups"
        )

    @pytest.mark.anyio
    async def test_empty_returns_message(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.months.resolve_budget",
            return_value=("budget-1", {}),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "money_movement_groups": [],
        }

        result = await list_money_movement_groups(mock_ctx)

        assert result == "No money movement groups found."
