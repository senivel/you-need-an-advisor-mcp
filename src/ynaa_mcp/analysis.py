"""MCP analysis prompt templates for YNAB budget analysis.

Provides 6 analysis prompts that guide LLMs through structured
data interpretation workflows: budget health, spending trends,
budget setup, debt payoff, savings goals, and income allocation.

Templates are loaded from .md files in the templates/analysis/
subpackage via importlib.resources.
"""

from importlib import resources as pkg_resources

from ynaa_mcp.app import mcp
from ynaa_mcp.prompts import _resolve_step


_templates = pkg_resources.files("ynaa_mcp.templates.analysis")

BUDGET_HEALTH_TEMPLATE = _templates.joinpath(
    "budget-health.md",
).read_text(encoding="utf-8")
SPENDING_TRENDS_TEMPLATE = _templates.joinpath(
    "spending-trends.md",
).read_text(encoding="utf-8")
BUDGET_SETUP_ADVISOR_TEMPLATE = _templates.joinpath(
    "budget-setup-advisor.md",
).read_text(encoding="utf-8")
DEBT_PAYOFF_PLANNER_TEMPLATE = _templates.joinpath(
    "debt-payoff-planner.md",
).read_text(encoding="utf-8")
SAVINGS_GOAL_TRACKER_TEMPLATE = _templates.joinpath(
    "savings-goal-tracker.md",
).read_text(encoding="utf-8")
INCOME_ALLOCATION_TEMPLATE = _templates.joinpath(
    "income-allocation.md",
).read_text(encoding="utf-8")


def _prepend_resolve_step(template: str) -> str:
    """Prepend the budget resolution step and renumber existing steps.

    When no budget_id is provided, the template needs a step 1 that
    instructs the LLM to resolve the budget ID first, with all
    existing steps renumbered starting from 2.

    Args:
        template: The formatted template text (with {budget_id} still
            as a literal placeholder).

    Returns:
        Template text with resolve step prepended and steps renumbered.
    """
    resolve = _resolve_step()
    lines = template.split("\n")
    header = lines[0]
    steps = []
    for line in lines[1:]:
        if line and line[0].isdigit():
            dot_idx = line.index(".")
            old_num = int(line[:dot_idx])
            steps.append(f"{old_num + 1}{line[dot_idx:]}")
        else:
            steps.append(line)
    return f"{header}\n\n{resolve}\n" + "\n".join(steps)


@mcp.prompt()
def budget_health_analysis(budget_id: str | None = None) -> str:
    """Comprehensive budget health assessment.

    Guides the LLM through checking TBB state, identifying
    overspending (cash vs credit), reviewing underfunded goals,
    and producing actionable improvement recommendations.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for budget health analysis.
    """
    if budget_id:
        return BUDGET_HEALTH_TEMPLATE.format(budget_id=budget_id)
    return _prepend_resolve_step(
        BUDGET_HEALTH_TEMPLATE.format(budget_id="{budget_id}"),
    )


@mcp.prompt()
def spending_trends(budget_id: str | None = None) -> str:
    """Multi-month spending comparison and trend analysis.

    Guides the LLM through fetching 3 months of transaction and
    category data, calculating month-over-month changes, and
    identifying categories with increasing or problematic trends.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for spending trend analysis.
    """
    if budget_id:
        return SPENDING_TRENDS_TEMPLATE.format(budget_id=budget_id)
    return _prepend_resolve_step(
        SPENDING_TRENDS_TEMPLATE.format(budget_id="{budget_id}"),
    )


@mcp.prompt()
def budget_setup_advisor(budget_id: str | None = None) -> str:
    """First-time YNAB budget setup guidance.

    Guides the LLM through creating accounts, organizing categories,
    performing initial budget allocation, and explaining the Four
    Rules in practical terms. Uses a supportive coaching tone.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for budget setup.
    """
    if budget_id:
        return BUDGET_SETUP_ADVISOR_TEMPLATE.format(budget_id=budget_id)
    return _prepend_resolve_step(
        BUDGET_SETUP_ADVISOR_TEMPLATE.format(budget_id="{budget_id}"),
    )


@mcp.prompt()
def debt_payoff_planner(budget_id: str | None = None) -> str:
    """Debt elimination strategy planner.

    Guides the LLM through identifying all debt accounts,
    presenting avalanche and snowball payoff strategies with
    trade-offs, and helping the user choose and implement a plan.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for debt payoff planning.
    """
    if budget_id:
        return DEBT_PAYOFF_PLANNER_TEMPLATE.format(budget_id=budget_id)
    return _prepend_resolve_step(
        DEBT_PAYOFF_PLANNER_TEMPLATE.format(budget_id="{budget_id}"),
    )


@mcp.prompt()
def savings_goal_tracker(budget_id: str | None = None) -> str:
    """Savings goal progress monitoring.

    Guides the LLM through listing all goals, calculating progress
    percentages, identifying underfunded goals, and creating
    prioritized funding recommendations.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for savings goal tracking.
    """
    if budget_id:
        return SAVINGS_GOAL_TRACKER_TEMPLATE.format(budget_id=budget_id)
    return _prepend_resolve_step(
        SAVINGS_GOAL_TRACKER_TEMPLATE.format(budget_id="{budget_id}"),
    )


@mcp.prompt()
def income_allocation(budget_id: str | None = None) -> str:
    """YNAB priority-ordered income allocation guidance.

    Guides the LLM through allocating new income following YNAB's
    recommended priority order: immediate obligations, true expenses,
    quality of life, and savings goals.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for income allocation.
    """
    if budget_id:
        return INCOME_ALLOCATION_TEMPLATE.format(budget_id=budget_id)
    return _prepend_resolve_step(
        INCOME_ALLOCATION_TEMPLATE.format(budget_id="{budget_id}"),
    )
