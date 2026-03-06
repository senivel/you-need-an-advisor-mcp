"""MCP Prompt templates for YNAB workflow guides.

Provides step-by-step workflow guides that help LLMs coach users
through common YNAB scenarios. Each prompt references specific MCP
resources to read and tools to call, with a supportive coaching tone.

Templates are loaded from .md files in the templates/workflows/
subpackage via importlib.resources.
"""

from importlib import resources as pkg_resources

from ynaa_mcp.app import mcp
from ynaa_mcp.prompts import resolve_step


_templates = pkg_resources.files("ynaa_mcp.templates.workflows")

GETTING_STARTED_TEMPLATE = _templates.joinpath(
    "getting-started.md",
).read_text(encoding="utf-8")
GETTING_OUT_OF_DEBT_TEMPLATE = _templates.joinpath(
    "getting-out-of-debt.md",
).read_text(encoding="utf-8")
IRREGULAR_INCOME_TEMPLATE = _templates.joinpath(
    "irregular-income.md",
).read_text(encoding="utf-8")
COUPLES_BUDGETING_TEMPLATE = _templates.joinpath(
    "couples-budgeting.md",
).read_text(encoding="utf-8")
EMERGENCY_FUND_TEMPLATE = _templates.joinpath(
    "emergency-fund.md",
).read_text(encoding="utf-8")
BREAKING_PAYCHECK_TO_PAYCHECK_TEMPLATE = _templates.joinpath(
    "breaking-paycheck-to-paycheck.md",
).read_text(encoding="utf-8")


def _format_with_resolve(template: str, budget_id: str | None) -> str:
    """Format a workflow template, inserting resolve step if needed.

    Args:
        template: The template string with {budget_id} placeholders.
        budget_id: Optional budget ID. If None, a resolve step is prepended.

    Returns:
        The formatted workflow guide text.
    """
    if budget_id:
        return template.format(budget_id=budget_id)

    resolve = resolve_step()
    body = template.format(budget_id="{budget_id}")
    lines = body.split("\n")
    header = lines[0]
    steps: list[str] = []
    for line in lines[1:]:
        if line and line[0].isdigit():
            dot_idx = line.index(".")
            old_num = int(line[:dot_idx])
            steps.append(f"{old_num + 1}{line[dot_idx:]}")
        else:
            steps.append(line)
    return f"{header}\n\n{resolve}\n" + "\n".join(steps)


@mcp.prompt()
def getting_started(budget_id: str | None = None) -> str:
    """Walk a new user through creating their first YNAB budget.

    Guides through account setup, category creation, and initial
    budget allocation with a supportive coaching tone.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Step-by-step first budget creation guide.
    """
    return _format_with_resolve(GETTING_STARTED_TEMPLATE, budget_id)


@mcp.prompt()
def getting_out_of_debt(budget_id: str | None = None) -> str:
    """Guide a user through building a debt payoff plan.

    Covers debt inventory, avalanche vs snowball strategies,
    and setting up systematic payment workflows.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Step-by-step debt payoff workflow guide.
    """
    return _format_with_resolve(GETTING_OUT_OF_DEBT_TEMPLATE, budget_id)


@mcp.prompt()
def irregular_income(budget_id: str | None = None) -> str:
    """Guide a freelancer or commission earner through income smoothing.

    Covers the income buffer concept, monthly workflow for variable
    income, and handling feast/famine cycles.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Step-by-step irregular income budgeting guide.
    """
    return _format_with_resolve(IRREGULAR_INCOME_TEMPLATE, budget_id)


@mcp.prompt()
def couples_budgeting(budget_id: str | None = None) -> str:
    """Guide a couple through setting up shared finances in YNAB.

    Covers budget structure options, account setup for partners,
    fun money categories, and the budget meeting workflow.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Step-by-step couples budgeting guide.
    """
    return _format_with_resolve(COUPLES_BUDGETING_TEMPLATE, budget_id)


@mcp.prompt()
def emergency_fund(budget_id: str | None = None) -> str:
    """Guide a user through building an emergency fund.

    Covers target calculation, category and goal setup,
    funding strategy, and when to use vs replenish.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Step-by-step emergency fund building guide.
    """
    return _format_with_resolve(EMERGENCY_FUND_TEMPLATE, budget_id)


@mcp.prompt()
def breaking_paycheck_to_paycheck(budget_id: str | None = None) -> str:
    """Guide a user through aging their money past 30 days.

    Covers the Age of Money concept, buffer building strategy,
    milestone tracking, and long-term maintenance.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Step-by-step guide to breaking the paycheck-to-paycheck cycle.
    """
    return _format_with_resolve(BREAKING_PAYCHECK_TO_PAYCHECK_TEMPLATE, budget_id)
