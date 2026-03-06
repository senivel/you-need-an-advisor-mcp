"""Tests for MCP workflow guide prompts."""

import pytest

import ynaa_mcp.workflows as workflows_module
from ynaa_mcp.workflows import (
    breaking_paycheck_to_paycheck,
    couples_budgeting,
    emergency_fund,
    getting_out_of_debt,
    getting_started,
    irregular_income,
)


# ---------------------------------------------------------------------------
# Parameterized fixtures for DRY testing across all 6 workflow guides
# ---------------------------------------------------------------------------

ALL_WORKFLOWS = [
    ("getting_started", getting_started),
    ("getting_out_of_debt", getting_out_of_debt),
    ("irregular_income", irregular_income),
    ("couples_budgeting", couples_budgeting),
    ("emergency_fund", emergency_fund),
    ("breaking_paycheck_to_paycheck", breaking_paycheck_to_paycheck),
]


@pytest.fixture(params=ALL_WORKFLOWS, ids=[w[0] for w in ALL_WORKFLOWS])
def workflow_fn(request):
    """Yield each workflow function in turn.

    Returns:
        The workflow callable for the current parametrize iteration.
    """
    return request.param[1]


class TestWorkflowCommon:
    """Tests that apply to all 6 workflow guides."""

    def test_with_budget_id_contains_id(self, workflow_fn):
        """When budget_id is provided, it appears in the output."""
        result = workflow_fn(budget_id="test-budget")
        assert "test-budget" in result

    def test_without_budget_id_contains_resolve(self, workflow_fn):
        """When budget_id is None, output includes manage_budgets resolve step."""
        result = workflow_fn(budget_id=None)
        assert "manage_budgets" in result

    def test_returns_substantial_content(self, workflow_fn):
        """Output is at least 200 characters long."""
        result = workflow_fn(budget_id="test-budget")
        assert isinstance(result, str)
        assert len(result) >= 200


class TestGettingStarted:
    """Tests for the getting_started workflow guide."""

    def test_references_terminology(self):
        result = getting_started(budget_id="b1")
        assert "ynab://knowledge/terminology" in result

    def test_references_manage_accounts(self):
        result = getting_started(budget_id="b1")
        assert "manage_accounts" in result

    def test_references_manage_categories(self):
        result = getting_started(budget_id="b1")
        assert "manage_categories" in result


class TestGettingOutOfDebt:
    """Tests for the getting_out_of_debt workflow guide."""

    def test_references_credit_cards(self):
        result = getting_out_of_debt(budget_id="b1")
        assert "ynab://knowledge/credit-cards" in result

    def test_references_overspending(self):
        result = getting_out_of_debt(budget_id="b1")
        assert "ynab://knowledge/overspending" in result

    def test_references_debt_strategies(self):
        result = getting_out_of_debt(budget_id="b1")
        text = result.lower()
        assert "avalanche" in text or "snowball" in text


class TestIrregularIncome:
    """Tests for the irregular_income workflow guide."""

    def test_references_terminology(self):
        result = irregular_income(budget_id="b1")
        assert "ynab://knowledge/terminology" in result

    def test_references_manage_categories(self):
        result = irregular_income(budget_id="b1")
        assert "manage_categories" in result

    def test_references_buffer_concept(self):
        result = irregular_income(budget_id="b1")
        text = result.lower()
        assert "buffer" in text or "income replacement" in text


class TestCouplesBudgeting:
    """Tests for the couples_budgeting workflow guide."""

    def test_references_terminology(self):
        result = couples_budgeting(budget_id="b1")
        assert "ynab://knowledge/terminology" in result

    def test_references_manage_accounts(self):
        result = couples_budgeting(budget_id="b1")
        assert "manage_accounts" in result

    def test_references_shared_finances(self):
        result = couples_budgeting(budget_id="b1")
        text = result.lower()
        assert "shared" in text or "joint" in text


class TestEmergencyFund:
    """Tests for the emergency_fund workflow guide."""

    def test_references_goals(self):
        result = emergency_fund(budget_id="b1")
        assert "ynab://knowledge/goals" in result

    def test_references_manage_categories(self):
        result = emergency_fund(budget_id="b1")
        assert "manage_categories" in result

    def test_references_months_of_expenses(self):
        result = emergency_fund(budget_id="b1")
        text = result.lower()
        assert "emergency" in text or "months of expenses" in text


class TestBreakingPaycheckToPaycheck:
    """Tests for the breaking_paycheck_to_paycheck workflow guide."""

    def test_references_terminology(self):
        result = breaking_paycheck_to_paycheck(budget_id="b1")
        assert "ynab://knowledge/terminology" in result

    def test_references_age_of_money(self):
        result = breaking_paycheck_to_paycheck(budget_id="b1")
        text = result.lower()
        assert "age of money" in text or "aging" in text


class TestWorkflowRegistration:
    """Tests for workflow module registration."""

    def test_at_least_six_workflow_functions(self):
        """At least 6 workflow functions exist in the module."""
        workflow_funcs = [
            name
            for name in dir(workflows_module)
            if not name.startswith("_")
            and callable(getattr(workflows_module, name))
            and name != "mcp"
        ]
        assert len(workflow_funcs) >= 6
