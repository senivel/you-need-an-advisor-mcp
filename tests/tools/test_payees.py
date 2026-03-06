"""Tests for manage_payees consolidated tool."""

import pytest
from fastmcp.exceptions import ToolError

from ynab_mcp.tools.payees import manage_payees


def _make_payee(
    *,
    payee_id="payee-001",
    name="Grocery Store",
    transfer_account_id=None,
    deleted=False,
):
    """Build a sample payee dict matching YNAB API shape."""
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
    """Build a sample payee location dict matching YNAB API shape."""
    return {
        "id": loc_id,
        "payee_id": payee_id,
        "latitude": latitude,
        "longitude": longitude,
        "deleted": deleted,
    }


class TestManagePayeesList:
    """Tests for manage_payees(action='list')."""

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

        result = await manage_payees(mock_ctx, action="list")

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

        result = await manage_payees(mock_ctx, action="list")

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

        result = await manage_payees(mock_ctx, action="list")

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

        result = await manage_payees(mock_ctx, action="list", include_transfers=True)

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

        result = await manage_payees(mock_ctx, action="list")

        assert result == "No payees found."


class TestManagePayeesGet:
    """Tests for manage_payees(action='get')."""

    @pytest.mark.anyio
    async def test_returns_payee_detail(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        payee = _make_payee(payee_id="p1", name="Grocery Store")
        mock_ctx.lifespan_context.client.get.return_value = {"payee": payee}

        result = await manage_payees(mock_ctx, action="get", payee_id="p1")

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

        result = await manage_payees(mock_ctx, action="get", payee_id="p1")

        assert "Transfer account: acct-999" in result

    @pytest.mark.anyio
    async def test_get_missing_id_raises(self, mock_ctx, mocker):
        """ToolError raised when payee_id is missing for get action."""
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )

        with pytest.raises(ToolError, match="payee_id is required"):
            await manage_payees(mock_ctx, action="get")


class TestManagePayeesUpdateName:
    """Tests for manage_payees(action='update_name')."""

    @pytest.mark.anyio
    async def test_renames_payee(self, mock_ctx, mocker):
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )
        mock_ctx.lifespan_context.client.patch.return_value = {
            "payee": _make_payee(payee_id="p1", name="New Name"),
        }

        result = await manage_payees(
            mock_ctx, action="update_name", payee_id="p1", name="New Name"
        )

        assert "Payee renamed" in result
        assert "New Name" in result
        assert "p1" in result
        mock_ctx.lifespan_context.client.patch.assert_called_once()


class TestManagePayeesListLocations:
    """Tests for manage_payees(action='list_locations')."""

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

        result = await manage_payees(mock_ctx, action="list_locations")

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

        result = await manage_payees(mock_ctx, action="list_locations", payee_id="p1")

        assert "1 payee location found:" in result
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

        result = await manage_payees(mock_ctx, action="list_locations")

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

        result = await manage_payees(mock_ctx, action="list_locations")

        assert result == "No payee locations found."


class TestManagePayeesGetLocation:
    """Tests for manage_payees(action='get_location')."""

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

        result = await manage_payees(
            mock_ctx, action="get_location", payee_location_id="loc-1"
        )

        assert "loc-1" in result
        assert "p1" in result
        assert "40.7128" in result
        assert "-74.006" in result

    @pytest.mark.anyio
    async def test_get_location_missing_id_raises(self, mock_ctx, mocker):
        """ToolError raised when payee_location_id is missing."""
        mocker.patch(
            "ynab_mcp.tools.payees.resolve_budget",
            return_value=("budget-1", {}),
        )

        with pytest.raises(ToolError, match="payee_location_id is required"):
            await manage_payees(mock_ctx, action="get_location")
