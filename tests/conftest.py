"""Shared test fixtures for YNAB MCP server tests."""

import pytest
from ynab_mcp.errors import YNABAPIError


def mock_ynab_error_response(
    status_code: int,
    error_id: str,
    name: str,
    detail: str,
) -> YNABAPIError:
    """Factory for creating YNABAPIError instances in tests.

    Args:
        status_code: HTTP status code.
        error_id: YNAB error ID (e.g., "404.2").
        name: YNAB error name (e.g., "resource_not_found").
        detail: Human-readable error detail.

    Returns:
        A configured YNABAPIError instance.
    """
    return YNABAPIError(
        status_code=status_code,
        error_id=error_id,
        name=name,
        detail=detail,
    )


@pytest.fixture
def sample_budget_response():
    """Return a dict matching YNAB GET /budgets response shape."""
    return {
        "data": {
            "budgets": [
                {
                    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "name": "My Budget",
                    "last_modified_on": "2026-03-01T12:00:00+00:00",
                    "first_month": "2024-01-01",
                    "last_month": "2026-03-01",
                    "date_format": {"format": "MM/DD/YYYY"},
                    "currency_format": {"iso_code": "USD"},
                }
            ],
            "default_budget": None,
        }
    }


@pytest.fixture
def sample_user_response():
    """Return a dict matching YNAB GET /user response shape."""
    return {
        "data": {
            "user": {
                "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            }
        }
    }
