"""Tests for payee tools: list, get, update, and payee location tools."""

import pytest

from ynab_mcp.tools.payees import (
    get_payee,
    get_payee_location,
    list_payee_locations,
    list_payees,
    update_payee_name,
)


def _make_payee(
    *,
    payee_id="payee-001",
    name="Grocery Store",
    transfer_account_id=None,
    deleted=False,
):
    """Build a sample payee dict matching YNAB API shape.

    Returns:
        Dict with payee fields.
    """
    return {
        "id": payee_id,
        "name": name,
        "transfer_account_id": transfer_account_id,
        "deleted": deleted,
    }


def _make_payee_location(
    *,
    loc_id="loc-001",
    payee_id="payee-001",
    latitude=40.7128,
    longitude=-74.0060,
    deleted=False,
):
    """Build a sample payee location dict matching YNAB API shape.

    Returns:
        Dict with payee location fields.
    """
    return {
        "id": loc_id,
        "payee_id": payee_id,
        "latitude": latitude,
        "longitude": longitude,
        "deleted": deleted,
    }


class TestListPayees:
    """Tests for list_payees tool (PAYE-01)."""

    @pytest.mark.anyio
    async def test_returns_payees_with_count_header(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        payees = [
            _make_payee(payee_id="p1", name="Grocery Store"),
            _make_payee(payee_id="p2", name="Gas Station"),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {"payees": payees}

        result = await list_payees(mock_ctx)

        assert "2 payees found:" in result
        assert "Grocery Store" in result
        assert "Gas Station" in result
        assert "p1" in result
        assert "p2" in result

    @pytest.mark.anyio
    async def test_excludes_deleted_payees(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        payees = [
            _make_payee(payee_id="p1", name="Active"),
            _make_payee(payee_id="p2", name="Deleted", deleted=True),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {"payees": payees}

        result = await list_payees(mock_ctx)

        assert "1 payee found:" in result
        assert "Active" in result
        assert "Deleted" not in result

    @pytest.mark.anyio
    async def test_excludes_transfers_by_default(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        payees = [
            _make_payee(payee_id="p1", name="Regular Payee"),
            _make_payee(
                payee_id="p2",
                name="Transfer: Savings",
                transfer_account_id="acct-999",
            ),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {"payees": payees}

        result = await list_payees(mock_ctx)

        assert "1 payee found:" in result
        assert "Regular Payee" in result
        assert "Transfer: Savings" not in result

    @pytest.mark.anyio
    async def test_includes_transfers_when_requested(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        payees = [
            _make_payee(payee_id="p1", name="Regular Payee"),
            _make_payee(
                payee_id="p2",
                name="Transfer: Savings",
                transfer_account_id="acct-999",
            ),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {"payees": payees}

        result = await list_payees(mock_ctx, include_transfers=True)

        assert "2 payees found:" in result
        assert "Regular Payee" in result
        assert "Transfer: Savings" in result

    @pytest.mark.anyio
    async def test_empty_returns_message(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        mock_ctx.lifespan_context.client.get.return_value = {"payees": []}

        result = await list_payees(mock_ctx)

        assert result == "No payees found."


class TestGetPayee:
    """Tests for get_payee tool (PAYE-02)."""

    @pytest.mark.anyio
    async def test_returns_payee_detail(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        payee = _make_payee(payee_id="p1", name="Grocery Store")
        mock_ctx.lifespan_context.client.get.return_value = {"payee": payee}

        result = await get_payee(mock_ctx, payee_id="p1")

        assert "Grocery Store" in result
        assert "p1" in result

    @pytest.mark.anyio
    async def test_shows_transfer_info(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        payee = _make_payee(
            payee_id="p1",
            name="Transfer: Savings",
            transfer_account_id="acct-999",
        )
        mock_ctx.lifespan_context.client.get.return_value = {"payee": payee}

        result = await get_payee(mock_ctx, payee_id="p1")

        assert "Transfer account: acct-999" in result


class TestUpdatePayeeName:
    """Tests for update_payee_name tool (PAYE-03)."""

    @pytest.mark.anyio
    async def test_renames_payee(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "payee": _make_payee(payee_id="p1", name="New Name"),
        }

        result = await update_payee_name(mock_ctx, payee_id="p1", name="New Name")

        assert "Payee renamed" in result
        assert "New Name" in result
        assert "p1" in result
        mock_ctx.lifespan_context.client.patch.assert_called_once()


class TestListPayeeLocations:
    """Tests for list_payee_locations tool (PAYE-04, PAYE-06)."""

    @pytest.mark.anyio
    async def test_returns_all_locations(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        locations = [
            _make_payee_location(loc_id="loc-1", payee_id="p1"),
            _make_payee_location(loc_id="loc-2", payee_id="p2"),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {
            "payee_locations": locations,
        }

        result = await list_payee_locations(mock_ctx)

        assert "2 payee locations found:" in result
        assert "loc-1" in result
        assert "loc-2" in result
        assert "40.7128" in result

    @pytest.mark.anyio
    async def test_filters_by_payee_id(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        locations = [
            _make_payee_location(loc_id="loc-1", payee_id="p1"),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {
            "payee_locations": locations,
        }

        result = await list_payee_locations(mock_ctx, payee_id="p1")

        assert "1 payee location found:" in result
        # Verify correct endpoint used
        mock_ctx.lifespan_context.client.get.assert_called_once()
        call_args = mock_ctx.lifespan_context.client.get.call_args
        assert "payees/p1/payee_locations" in call_args[0][0]

    @pytest.mark.anyio
    async def test_excludes_deleted_locations(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        locations = [
            _make_payee_location(loc_id="loc-1", deleted=False),
            _make_payee_location(loc_id="loc-2", deleted=True),
        ]
        mock_ctx.lifespan_context.client.get.return_value = {
            "payee_locations": locations,
        }

        result = await list_payee_locations(mock_ctx)

        assert "1 payee location found:" in result
        assert "loc-1" in result
        assert "loc-2" not in result

    @pytest.mark.anyio
    async def test_empty_returns_message(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "payee_locations": [],
        }

        result = await list_payee_locations(mock_ctx)

        assert result == "No payee locations found."


class TestGetPayeeLocation:
    """Tests for get_payee_location tool (PAYE-05)."""

    @pytest.mark.anyio
    async def test_returns_location_detail(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        location = _make_payee_location(
            loc_id="loc-1",
            payee_id="p1",
            latitude=40.7128,
            longitude=-74.0060,
        )
        mock_ctx.lifespan_context.client.get.return_value = {
            "payee_location": location,
        }

        result = await get_payee_location(mock_ctx, payee_location_id="loc-1")

        assert "loc-1" in result
        assert "p1" in result
        assert "40.7128" in result
        assert "-74.006" in result
