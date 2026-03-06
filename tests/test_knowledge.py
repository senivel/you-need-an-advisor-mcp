"""Tests for knowledge resources."""

import pytest

from ynab_mcp.knowledge import (
    CREDIT_CARDS_CONTENT,
    GOALS_CONTENT,
    OVERSPENDING_CONTENT,
    RECONCILIATION_CONTENT,
    TERMINOLOGY_CONTENT,
    credit_cards,
    goals,
    overspending,
    reconciliation,
    terminology,
)


class TestKnowledgeContent:
    """Verify markdown content is loaded and non-empty."""

    @pytest.mark.parametrize(
        ("content_var", "expected_heading"),
        [
            (TERMINOLOGY_CONTENT, "# YNAB Terminology"),
            (CREDIT_CARDS_CONTENT, "# Credit Card"),
            (GOALS_CONTENT, "# Goal Types"),
            (OVERSPENDING_CONTENT, "# Overspending"),
            (RECONCILIATION_CONTENT, "# Reconciliation"),
        ],
    )
    def test_content_loaded_and_has_heading(
        self, content_var: str, expected_heading: str
    ) -> None:
        assert len(content_var) > 100
        assert expected_heading in content_var


class TestKnowledgeResources:
    """Verify resource functions return loaded content."""

    def test_terminology_returns_content(self) -> None:
        assert terminology() == TERMINOLOGY_CONTENT

    def test_credit_cards_returns_content(self) -> None:
        assert credit_cards() == CREDIT_CARDS_CONTENT

    def test_goals_returns_content(self) -> None:
        assert goals() == GOALS_CONTENT

    def test_overspending_returns_content(self) -> None:
        assert overspending() == OVERSPENDING_CONTENT

    def test_reconciliation_returns_content(self) -> None:
        assert reconciliation() == RECONCILIATION_CONTENT
