"""Tests for milliunit/dollar conversion and base Pydantic models."""

from ynab_mcp.converters import dollars_to_milliunits, milliunits_to_dollars
from ynab_mcp.models import BudgetsResponse, BudgetSummary, ErrorDetail, ErrorResponse


class TestMilliunitsToDollars:
    """Tests for milliunits_to_dollars conversion."""

    def test_standard_conversion(self):
        assert milliunits_to_dollars(45670) == 45.67

    def test_zero(self):
        assert milliunits_to_dollars(0) == 0.0

    def test_negative_amount(self):
        assert milliunits_to_dollars(-45670) == -45.67

    def test_large_amount(self):
        assert milliunits_to_dollars(1000000000) == 1000000.0


class TestDollarsToMilliunits:
    """Tests for dollars_to_milliunits conversion."""

    def test_standard_conversion(self):
        assert dollars_to_milliunits(45.67) == 45670

    def test_zero(self):
        assert dollars_to_milliunits(0.0) == 0

    def test_negative_amount(self):
        assert dollars_to_milliunits(-45.67) == -45670

    def test_sub_cent_precision_rounds(self):
        """Sub-cent precision should round to nearest milliunit."""
        assert dollars_to_milliunits(45.6789) == 45679

    def test_float_precision_edge_case(self):
        """0.1 + 0.2 should convert to 300, not 299 or 301."""
        assert dollars_to_milliunits(0.1 + 0.2) == 300


class TestBudgetSummaryModel:
    """Tests for BudgetSummary Pydantic model."""

    def test_validates_from_api_response(self):
        data = {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "name": "My Budget",
            "last_modified_on": "2026-03-01T12:00:00+00:00",
            "first_month": "2024-01-01",
            "last_month": "2026-03-01",
        }
        budget = BudgetSummary.model_validate(data)
        assert budget.id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        assert budget.name == "My Budget"

    def test_ignores_extra_fields(self):
        data = {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "name": "My Budget",
            "last_modified_on": "2026-03-01T12:00:00+00:00",
            "first_month": "2024-01-01",
            "last_month": "2026-03-01",
            "date_format": {"format": "MM/DD/YYYY"},
            "currency_format": {"iso_code": "USD"},
        }
        budget = BudgetSummary.model_validate(data)
        assert budget.name == "My Budget"

    def test_budgets_response_wraps_list(self):
        data = {
            "budgets": [
                {
                    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "name": "My Budget",
                    "last_modified_on": "2026-03-01T12:00:00+00:00",
                    "first_month": "2024-01-01",
                    "last_month": "2026-03-01",
                }
            ]
        }
        response = BudgetsResponse.model_validate(data)
        assert len(response.budgets) == 1
        assert response.budgets[0].name == "My Budget"


class TestErrorResponseModel:
    """Tests for ErrorResponse Pydantic model."""

    def test_validates_from_api_error(self):
        data = {
            "error": {
                "id": "404.2",
                "name": "resource_not_found",
                "detail": "Budget not found",
            }
        }
        response = ErrorResponse.model_validate(data)
        assert response.error.id == "404.2"
        assert response.error.name == "resource_not_found"
        assert response.error.detail == "Budget not found"

    def test_error_detail_fields(self):
        data = {
            "id": "429",
            "name": "too_many_requests",
            "detail": "Too many requests",
        }
        detail = ErrorDetail.model_validate(data)
        assert detail.id == "429"
        assert detail.name == "too_many_requests"
