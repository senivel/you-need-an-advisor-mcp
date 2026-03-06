"""Tests for MCP analysis prompt templates."""

import ynab_mcp.analysis as analysis_module
from ynab_mcp.analysis import (
    BUDGET_HEALTH_TEMPLATE,
    BUDGET_SETUP_ADVISOR_TEMPLATE,
    DEBT_PAYOFF_PLANNER_TEMPLATE,
    INCOME_ALLOCATION_TEMPLATE,
    SAVINGS_GOAL_TRACKER_TEMPLATE,
    SPENDING_TRENDS_TEMPLATE,
    budget_health_analysis,
    budget_setup_advisor,
    debt_payoff_planner,
    income_allocation,
    savings_goal_tracker,
    spending_trends,
)


# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------


class TestTemplateConstants:
    """Tests for template loading via importlib.resources."""

    def test_budget_health_template_loaded(self):
        assert isinstance(BUDGET_HEALTH_TEMPLATE, str)
        assert len(BUDGET_HEALTH_TEMPLATE) > 0

    def test_spending_trends_template_loaded(self):
        assert isinstance(SPENDING_TRENDS_TEMPLATE, str)
        assert len(SPENDING_TRENDS_TEMPLATE) > 0

    def test_budget_setup_advisor_template_loaded(self):
        assert isinstance(BUDGET_SETUP_ADVISOR_TEMPLATE, str)
        assert len(BUDGET_SETUP_ADVISOR_TEMPLATE) > 0

    def test_debt_payoff_planner_template_loaded(self):
        assert isinstance(DEBT_PAYOFF_PLANNER_TEMPLATE, str)
        assert len(DEBT_PAYOFF_PLANNER_TEMPLATE) > 0

    def test_savings_goal_tracker_template_loaded(self):
        assert isinstance(SAVINGS_GOAL_TRACKER_TEMPLATE, str)
        assert len(SAVINGS_GOAL_TRACKER_TEMPLATE) > 0

    def test_income_allocation_template_loaded(self):
        assert isinstance(INCOME_ALLOCATION_TEMPLATE, str)
        assert len(INCOME_ALLOCATION_TEMPLATE) > 0


# ---------------------------------------------------------------------------
# Budget Health Analysis (PROMPT-01)
# ---------------------------------------------------------------------------


class TestBudgetHealthAnalysis:
    """Tests for budget_health_analysis prompt."""

    def test_with_budget_id(self):
        result = budget_health_analysis(budget_id="test-budget")
        assert "test-budget" in result

    def test_without_budget_id(self):
        result = budget_health_analysis()
        assert "manage_budgets" in result

    def test_substantive_content(self):
        result = budget_health_analysis(budget_id="test-budget")
        assert len(result) >= 200

    def test_references_manage_budgets(self):
        result = budget_health_analysis(budget_id="test-budget")
        assert "manage_budgets" in result

    def test_references_manage_categories(self):
        result = budget_health_analysis(budget_id="test-budget")
        assert "manage_categories" in result

    def test_references_tbb(self):
        result = budget_health_analysis(budget_id="test-budget")
        assert "To Be Budgeted" in result or "TBB" in result


# ---------------------------------------------------------------------------
# Spending Trends (PROMPT-02)
# ---------------------------------------------------------------------------


class TestSpendingTrends:
    """Tests for spending_trends prompt."""

    def test_with_budget_id(self):
        result = spending_trends(budget_id="test-budget")
        assert "test-budget" in result

    def test_without_budget_id(self):
        result = spending_trends()
        assert "manage_budgets" in result

    def test_substantive_content(self):
        result = spending_trends(budget_id="test-budget")
        assert len(result) >= 200

    def test_references_manage_months(self):
        result = spending_trends(budget_id="test-budget")
        assert "manage_months" in result

    def test_references_manage_transactions(self):
        result = spending_trends(budget_id="test-budget")
        assert "manage_transactions" in result

    def test_references_comparison(self):
        """Template mentions comparing across months."""
        result = spending_trends(budget_id="test-budget")
        text = result.lower()
        assert "compar" in text or "trend" in text or "month-over-month" in text


# ---------------------------------------------------------------------------
# Budget Setup Advisor (PROMPT-03)
# ---------------------------------------------------------------------------


class TestBudgetSetupAdvisor:
    """Tests for budget_setup_advisor prompt."""

    def test_with_budget_id(self):
        result = budget_setup_advisor(budget_id="test-budget")
        assert "test-budget" in result

    def test_without_budget_id(self):
        result = budget_setup_advisor()
        assert "manage_budgets" in result

    def test_substantive_content(self):
        result = budget_setup_advisor(budget_id="test-budget")
        assert len(result) >= 200

    def test_references_terminology_resource(self):
        result = budget_setup_advisor(budget_id="test-budget")
        assert "ynab://knowledge/terminology" in result

    def test_references_manage_accounts(self):
        result = budget_setup_advisor(budget_id="test-budget")
        assert "manage_accounts" in result

    def test_references_manage_categories(self):
        result = budget_setup_advisor(budget_id="test-budget")
        assert "manage_categories" in result


# ---------------------------------------------------------------------------
# Debt Payoff Planner (PROMPT-04)
# ---------------------------------------------------------------------------


class TestDebtPayoffPlanner:
    """Tests for debt_payoff_planner prompt."""

    def test_with_budget_id(self):
        result = debt_payoff_planner(budget_id="test-budget")
        assert "test-budget" in result

    def test_without_budget_id(self):
        result = debt_payoff_planner()
        assert "manage_budgets" in result

    def test_substantive_content(self):
        result = debt_payoff_planner(budget_id="test-budget")
        assert len(result) >= 200

    def test_references_credit_cards_resource(self):
        result = debt_payoff_planner(budget_id="test-budget")
        assert "ynab://knowledge/credit-cards" in result

    def test_references_overspending_resource(self):
        result = debt_payoff_planner(budget_id="test-budget")
        assert "ynab://knowledge/overspending" in result

    def test_presents_avalanche_strategy(self):
        result = debt_payoff_planner(budget_id="test-budget")
        assert "avalanche" in result.lower()

    def test_presents_snowball_strategy(self):
        result = debt_payoff_planner(budget_id="test-budget")
        assert "snowball" in result.lower()


# ---------------------------------------------------------------------------
# Savings Goal Tracker (PROMPT-05)
# ---------------------------------------------------------------------------


class TestSavingsGoalTracker:
    """Tests for savings_goal_tracker prompt."""

    def test_with_budget_id(self):
        result = savings_goal_tracker(budget_id="test-budget")
        assert "test-budget" in result

    def test_without_budget_id(self):
        result = savings_goal_tracker()
        assert "manage_budgets" in result

    def test_substantive_content(self):
        result = savings_goal_tracker(budget_id="test-budget")
        assert len(result) >= 200

    def test_references_goals_resource(self):
        result = savings_goal_tracker(budget_id="test-budget")
        assert "ynab://knowledge/goals" in result

    def test_references_manage_categories(self):
        result = savings_goal_tracker(budget_id="test-budget")
        assert "manage_categories" in result


# ---------------------------------------------------------------------------
# Income Allocation (PROMPT-06)
# ---------------------------------------------------------------------------


class TestIncomeAllocation:
    """Tests for income_allocation prompt."""

    def test_with_budget_id(self):
        result = income_allocation(budget_id="test-budget")
        assert "test-budget" in result

    def test_without_budget_id(self):
        result = income_allocation()
        assert "manage_budgets" in result

    def test_substantive_content(self):
        result = income_allocation(budget_id="test-budget")
        assert len(result) >= 200

    def test_references_manage_categories(self):
        result = income_allocation(budget_id="test-budget")
        assert "manage_categories" in result

    def test_priority_ordering(self):
        """Template references YNAB priority ordering."""
        result = income_allocation(budget_id="test-budget")
        text = result.lower()
        assert "immediate obligations" in text or "immediate" in text
        assert "true expenses" in text or "sinking fund" in text
        assert "quality of life" in text
        assert "savings" in text


# ---------------------------------------------------------------------------
# Module registration
# ---------------------------------------------------------------------------


class TestAnalysisRegistration:
    """Tests for analysis module registration."""

    def test_six_prompt_functions_exist(self):
        prompt_funcs = [
            name
            for name in dir(analysis_module)
            if not name.startswith("_")
            and callable(getattr(analysis_module, name))
            and name not in {"mcp", "pkg_resources", "analysis_module"}
        ]
        # At least 6 public callable objects (the prompt functions)
        assert len(prompt_funcs) >= 6
