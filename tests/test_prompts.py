"""Tests for MCP Prompt templates: spending review, transaction entry, health check."""

import ynab_mcp.prompts as prompts_module
from ynab_mcp.prompts import (
    BUDGET_HEALTH_TEMPLATE,
    ENTER_TRANSACTIONS_TEMPLATE,
    REVIEW_SPENDING_TEMPLATE,
    budget_health_check,
    enter_transactions,
    review_monthly_spending,
)


class TestTemplateConstants:
    """Tests for template loading."""

    def test_review_spending_template_loaded(self):
        """Template constant is a non-empty string."""
        assert isinstance(REVIEW_SPENDING_TEMPLATE, str)
        assert len(REVIEW_SPENDING_TEMPLATE) > 0

    def test_enter_transactions_template_loaded(self):
        """Template constant is a non-empty string."""
        assert isinstance(ENTER_TRANSACTIONS_TEMPLATE, str)
        assert len(ENTER_TRANSACTIONS_TEMPLATE) > 0

    def test_budget_health_template_loaded(self):
        """Template constant is a non-empty string."""
        assert isinstance(BUDGET_HEALTH_TEMPLATE, str)
        assert len(BUDGET_HEALTH_TEMPLATE) > 0

    def test_review_spending_format_placeholders(self):
        """Template can be formatted without errors."""
        result = REVIEW_SPENDING_TEMPLATE.format(
            budget_id="test-id",
            month="2026-03",
        )
        assert "test-id" in result
        assert "2026-03" in result

    def test_enter_transactions_format_placeholders(self):
        """Template can be formatted without errors."""
        result = ENTER_TRANSACTIONS_TEMPLATE.format(budget_id="test-id")
        assert "test-id" in result

    def test_budget_health_format_placeholders(self):
        """Template can be formatted without errors."""
        result = BUDGET_HEALTH_TEMPLATE.format(budget_id="test-id")
        assert "test-id" in result


class TestReviewMonthlySpending:
    """Tests for review_monthly_spending prompt."""

    def test_returns_string(self):
        """Prompt returns a non-empty string."""
        result = review_monthly_spending(month="2026-03")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_references_tools(self):
        """Output mentions required consolidated tool names."""
        result = review_monthly_spending(month="2026-03")

        assert "manage_transactions" in result
        assert "manage_months" in result

    def test_references_resources(self):
        """Output mentions ynab:// resource URI."""
        result = review_monthly_spending(
            month="2026-03",
            budget_id="budget-123",
        )

        assert "ynab://" in result

    def test_with_budget_id(self):
        """Budget ID is included in output when provided."""
        result = review_monthly_spending(
            month="2026-03",
            budget_id="budget-123",
        )

        assert "budget-123" in result

    def test_without_budget_id(self):
        """Fallback instruction to resolve budget when not provided."""
        result = review_monthly_spending(month="2026-03")

        assert "manage_budgets" in result


class TestEnterTransactions:
    """Tests for enter_transactions prompt."""

    def test_references_create_tool(self):
        """Output mentions manage_transactions tool."""
        result = enter_transactions()

        assert "manage_transactions" in result

    def test_with_budget_id(self):
        """Budget ID is included in output when provided."""
        result = enter_transactions(budget_id="budget-456")

        assert "budget-456" in result

    def test_without_budget_id(self):
        """Fallback instruction when no budget_id."""
        result = enter_transactions()

        assert "manage_budgets" in result


class TestBudgetHealthCheck:
    """Tests for budget_health_check prompt."""

    def test_returns_string(self):
        """Prompt returns a non-empty string."""
        result = budget_health_check()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_with_budget_id(self):
        """Budget ID included when provided."""
        result = budget_health_check(budget_id="budget-789")

        assert "budget-789" in result

    def test_without_budget_id(self):
        """Fallback instruction when no budget_id."""
        result = budget_health_check()

        assert "manage_budgets" in result


class TestPromptRegistration:
    """Tests for prompt module registration."""

    def test_at_least_two_prompts_registered(self):
        """At least 2 prompt functions exist in the module."""
        prompt_funcs = [
            name
            for name in dir(prompts_module)
            if not name.startswith("_")
            and callable(getattr(prompts_module, name))
            and name != "mcp"
        ]

        assert len(prompt_funcs) >= 2
