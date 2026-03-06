"""Tests for budget resolution logic."""

import pytest
from fastmcp.exceptions import ToolError

from ynaa_mcp.budget_resolver import resolve_budget
from ynaa_mcp.cache import CacheStore


def _make_budget(budget_id, name):
    """Create a budget dict as returned by YNABClient.get('/budgets').

    Returns:
        A dict matching the BudgetSummary shape.
    """
    return {
        "id": budget_id,
        "name": name,
        "last_modified_on": "2026-03-01T12:00:00+00:00",
        "first_month": "2024-01-01",
        "last_month": "2026-03-01",
    }


BUDGET_A = _make_budget("aaaa-1111", "My Budget")
BUDGET_B = _make_budget("bbbb-2222", "Vacation Fund")


def _mock_client(mocker, budgets):
    """Create a mock YNABClient that returns the given budgets list.

    Returns:
        An AsyncMock configured to return the given budgets.
    """
    client = mocker.AsyncMock()
    client.get.return_value = {"budgets": budgets}
    return client


class TestNoBudgetIdProvided:
    """Tests for when budget_id_or_name is None."""

    @pytest.mark.anyio
    async def test_single_budget_returns_that_budget_id(self, mocker):
        """Single budget auto-selects and returns its ID."""
        client = _mock_client(mocker, [BUDGET_A])
        budget_id, _message = await resolve_budget(client)

        assert budget_id == "aaaa-1111"

    @pytest.mark.anyio
    async def test_single_budget_message_includes_name(self, mocker):
        """Auto-selected budget message contains the budget name."""
        client = _mock_client(mocker, [BUDGET_A])
        _, message = await resolve_budget(client)

        assert message is not None
        assert "My Budget" in message

    @pytest.mark.anyio
    async def test_multiple_budgets_raises_tool_error(self, mocker):
        """Multiple budgets without ID raises ToolError listing all budgets."""
        client = _mock_client(mocker, [BUDGET_A, BUDGET_B])

        with pytest.raises(ToolError) as exc_info:
            await resolve_budget(client)

        error_msg = str(exc_info.value)
        assert "aaaa-1111" in error_msg
        assert "bbbb-2222" in error_msg
        assert "My Budget" in error_msg
        assert "Vacation Fund" in error_msg

    @pytest.mark.anyio
    async def test_no_budgets_raises_tool_error(self, mocker):
        """Empty budget list raises ToolError with clear message."""
        client = _mock_client(mocker, [])

        with pytest.raises(ToolError, match="No budgets found"):
            await resolve_budget(client)


class TestExactUUIDMatch:
    """Tests for when budget_id_or_name is an exact UUID."""

    @pytest.mark.anyio
    async def test_exact_uuid_match_returns_budget_id(self, mocker):
        """Exact UUID match returns the budget ID with no message."""
        client = _mock_client(mocker, [BUDGET_A, BUDGET_B])
        budget_id, message = await resolve_budget(client, "bbbb-2222")

        assert budget_id == "bbbb-2222"
        assert message is None


class TestFuzzyNameMatch:
    """Tests for fuzzy name matching."""

    @pytest.mark.anyio
    async def test_case_insensitive_match(self, mocker):
        """Case-insensitive name matches the correct budget."""
        client = _mock_client(mocker, [BUDGET_A, BUDGET_B])
        budget_id, _message = await resolve_budget(client, "my budget")

        assert budget_id == "aaaa-1111"

    @pytest.mark.anyio
    async def test_low_similarity_raises_tool_error(self, mocker):
        """Low similarity name (< 0.6 ratio) raises ToolError."""
        client = _mock_client(mocker, [BUDGET_A, BUDGET_B])

        with pytest.raises(ToolError, match="No budget found matching"):
            await resolve_budget(client, "zzzzz totally wrong")


class TestBudgetCacheIntegration:
    """Tests for resolve_budget with TTL cache."""

    @pytest.mark.anyio
    async def test_cached_budget_list_avoids_api_call(self, mocker):
        """Second resolve_budget call uses cache, no API hit."""
        mock_time = mocker.patch("ynaa_mcp.cache.time")
        mock_time.monotonic.return_value = 1000.0

        client = _mock_client(mocker, [BUDGET_A])
        cache = CacheStore()

        # First call -- hits API
        budget_id_1, _ = await resolve_budget(client, "aaaa-1111", cache=cache)
        assert budget_id_1 == "aaaa-1111"
        assert client.get.call_count == 1

        # Second call -- should use cache
        mock_time.monotonic.return_value = 1100.0
        budget_id_2, _ = await resolve_budget(client, "aaaa-1111", cache=cache)
        assert budget_id_2 == "aaaa-1111"
        assert client.get.call_count == 1  # Still 1 -- no extra API call

    @pytest.mark.anyio
    async def test_expired_cache_fetches_from_api(self, mocker):
        """resolve_budget fetches from API when TTL expired."""
        mock_time = mocker.patch("ynaa_mcp.cache.time")
        mock_time.monotonic.return_value = 1000.0

        client = _mock_client(mocker, [BUDGET_A])
        cache = CacheStore()

        # First call
        await resolve_budget(client, "aaaa-1111", cache=cache)
        assert client.get.call_count == 1

        # Expire the TTL (> 300 seconds later)
        mock_time.monotonic.return_value = 1301.0
        await resolve_budget(client, "aaaa-1111", cache=cache)
        assert client.get.call_count == 2  # Had to re-fetch

    @pytest.mark.anyio
    async def test_resolve_budget_works_without_cache(self, mocker):
        """resolve_budget works without cache parameter (backward compat)."""
        client = _mock_client(mocker, [BUDGET_A])

        budget_id, _ = await resolve_budget(client, "aaaa-1111")
        assert budget_id == "aaaa-1111"
        assert client.get.call_count == 1
