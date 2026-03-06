"""Budget auto-resolution logic for YNAB MCP tools.

Provides ``resolve_budget()`` which resolves a budget identifier
(UUID or fuzzy name) to a budget ID. Used by all tools that operate
on a specific budget.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from fastmcp.exceptions import ToolError

from ynab_mcp.models import BudgetsResponse


if TYPE_CHECKING:
    from ynab_mcp.cache import CacheStore
    from ynab_mcp.client import YNABClient


_FUZZY_MATCH_THRESHOLD = 0.6
"""Minimum SequenceMatcher ratio for a fuzzy name match."""

_BUDGET_LIST_TTL = 300.0
"""TTL in seconds for cached budget list (5 minutes)."""


async def resolve_budget(
    client: YNABClient,
    budget_id_or_name: str | None = None,
    *,
    cache: CacheStore | None = None,
) -> tuple[str, str | None]:
    """Resolve a budget identifier to a budget ID.

    Fetches the list of budgets from the YNAB API and resolves the
    given identifier to a concrete budget ID. Supports three modes:

    1. **No identifier:** Auto-selects if exactly one budget exists,
       otherwise lists available budgets in the error message.
    2. **UUID:** Returns the ID directly if it matches a known budget.
    3. **Fuzzy name:** Case-insensitive fuzzy matching using
       ``difflib.SequenceMatcher`` with a threshold of 0.6.

    Args:
        client: The YNAB API client instance.
        budget_id_or_name: Optional budget UUID or name to resolve.
        cache: Optional CacheStore for TTL-based budget list caching.

    Returns:
        A tuple of ``(budget_id, info_message)`` where ``info_message``
        is None or an informational note about how the budget was resolved.

    Raises:
        ToolError: If resolution fails (no budgets, ambiguous, no match).
    """
    cached_data = cache.get_ttl("budgets") if cache else None
    if cached_data is not None:
        data = cached_data
    else:
        data = await client.get("/budgets")
        if cache is not None:
            cache.set_ttl("budgets", data, ttl_seconds=_BUDGET_LIST_TTL)
    budgets_response = BudgetsResponse.model_validate(data)
    budgets = budgets_response.budgets

    if not budgets:
        msg = "No budgets found. Create a budget at app.ynab.com first."
        raise ToolError(msg)

    if budget_id_or_name is None:
        return _resolve_without_identifier(budgets)

    return _resolve_with_identifier(budgets, budget_id_or_name)


def _resolve_without_identifier(
    budgets: list,
) -> tuple[str, str | None]:
    """Resolve when no identifier is provided.

    Args:
        budgets: List of BudgetSummary models.

    Returns:
        Tuple of (budget_id, info_message).

    Raises:
        ToolError: If multiple budgets exist (ambiguous).
    """
    if len(budgets) == 1:
        budget = budgets[0]
        return budget.id, f"Using budget '{budget.name}' (only budget found)"

    lines = [f"- {b.name} (ID: {b.id})" for b in budgets]
    msg = "Multiple budgets found. Please specify a budget_id or name:\n" + "\n".join(
        lines
    )
    raise ToolError(msg)


def _resolve_with_identifier(
    budgets: list,
    budget_id_or_name: str,
) -> tuple[str, str | None]:
    """Resolve using a UUID or fuzzy name match.

    Args:
        budgets: List of BudgetSummary models.
        budget_id_or_name: The UUID or name to match.

    Returns:
        Tuple of (budget_id, info_message).

    Raises:
        ToolError: If no matching budget is found.
    """
    # Try exact UUID match first
    for budget in budgets:
        if budget.id == budget_id_or_name:
            return budget.id, None

    # Try fuzzy name match
    best_match = None
    best_ratio = 0.0
    query_lower = budget_id_or_name.lower()

    for budget in budgets:
        ratio = SequenceMatcher(None, query_lower, budget.name.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = budget

    if best_match is not None and best_ratio >= _FUZZY_MATCH_THRESHOLD:
        note = f"Matched budget '{best_match.name}' (similarity: {best_ratio:.0%})"
        return best_match.id, note

    lines = [f"- {b.name} (ID: {b.id})" for b in budgets]
    msg = (
        f"No budget found matching '{budget_id_or_name}'. "
        f"Available budgets:\n" + "\n".join(lines)
    )
    raise ToolError(msg)
