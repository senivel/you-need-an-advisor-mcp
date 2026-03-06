"""Tests for manage_budgets consolidated tool."""

import pytest

from ynaa_mcp.tools.budgets import manage_budgets


def _make_budget_get_side_effect():
    """Create a side_effect for client.get that handles budget and settings.

    Returns:
        A function suitable for use as side_effect on an AsyncMock.
    """

    def fake_get(path, **_kwargs):
        if "settings" in path:
            return {
                "settings": {
                    "date_format": {"format": "MM/DD/YYYY"},
                    "currency_format": {"iso_code": "USD"},
                }
            }
        return {
            "budget": {
                "id": "budget-123",
                "name": "My Budget",
                "first_month": "2024-01-01",
                "last_month": "2026-03-01",
            }
        }

    return fake_get


class TestManageBudgetsList:
    """Tests for manage_budgets(action='list')."""

    @pytest.mark.anyio
    async def test_returns_count_header_and_budget_list(self, mock_ctx):
        mock_ctx.lifespan_context.client.get.return_value = {
            "budgets": [
                {
                    "id": "aaa-111",
                    "name": "My Budget",
                    "last_modified_on": "2026-03-01T12:00:00+00:00",
                    "first_month": "2024-01-01",
                    "last_month": "2026-03-01",
                },
                {
                    "id": "bbb-222",
                    "name": "Side Budget",
                    "last_modified_on": "2026-02-15T10:00:00+00:00",
                    "first_month": "2025-01-01",
                    "last_month": "2026-02-01",
                },
            ]
        }

        result = await manage_budgets(mock_ctx, action="list")

        assert "2 budgets found:" in result
        assert "My Budget" in result
        assert "aaa-111" in result
        assert "Side Budget" in result
        assert "2026-03-01" in result

    @pytest.mark.anyio
    async def test_empty_budgets(self, mock_ctx):
        mock_ctx.lifespan_context.client.get.return_value = {"budgets": []}

        result = await manage_budgets(mock_ctx, action="list")

        assert result == "No budgets found."


class TestManageBudgetsGet:
    """Tests for manage_budgets(action='get')."""

    @pytest.mark.anyio
    async def test_returns_budget_detail_with_settings(self, mock_ctx, mocker):
        mocker.patch(
            "ynaa_mcp.tools.budgets.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_client = mock_ctx.lifespan_context.client
        mock_client.get.side_effect = _make_budget_get_side_effect()

        result = await manage_budgets(mock_ctx, action="get")

        assert "My Budget" in result
        assert "2024-01-01" in result
        assert "2026-03-01" in result
        assert "MM/DD/YYYY" in result
        assert "USD" in result

    @pytest.mark.anyio
    async def test_prepends_info_message(self, mock_ctx, mocker):
        mocker.patch(
            "ynaa_mcp.tools.budgets.resolve_budget",
            return_value=(
                "budget-123",
                "Using budget 'My Budget' (only budget found)",
            ),
        )
        mock_client = mock_ctx.lifespan_context.client
        mock_client.get.side_effect = _make_budget_get_side_effect()

        result = await manage_budgets(mock_ctx, action="get")

        assert result.startswith("Using budget 'My Budget' (only budget found)")

    @pytest.mark.anyio
    async def test_passes_budget_id_or_name_to_resolver(self, mock_ctx, mocker):
        mock_resolve = mocker.patch(
            "ynaa_mcp.tools.budgets.resolve_budget",
            return_value=("budget-123", None),
        )
        mock_client = mock_ctx.lifespan_context.client
        mock_client.get.side_effect = _make_budget_get_side_effect()

        await manage_budgets(mock_ctx, action="get", budget_id_or_name="My Budget")

        mock_resolve.assert_called_once_with(
            mock_client, "My Budget", cache=mock_ctx.lifespan_context.cache
        )


class TestManageBudgetsGetUser:
    """Tests for manage_budgets(action='get_user')."""

    @pytest.mark.anyio
    async def test_returns_user_id(self, mock_ctx):
        mock_ctx.lifespan_context.client.get.return_value = {
            "user": {
                "id": "user-abc-123",
            }
        }

        result = await manage_budgets(mock_ctx, action="get_user")

        assert "user-abc-123" in result
        assert "User ID" in result
