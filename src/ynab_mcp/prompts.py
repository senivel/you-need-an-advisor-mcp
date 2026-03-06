"""MCP Prompt templates for common YNAB workflows.

Provides guided workflow instructions that help LLMs perform
multi-step YNAB tasks efficiently. Each prompt references the
specific MCP resources to read and tools to call.

Templates are loaded from .md files in the templates/prompts/
subpackage via importlib.resources.
"""

from importlib import resources as pkg_resources

from ynab_mcp.app import mcp


_RESOURCE_BASE = "ynab://budgets"

_templates = pkg_resources.files("ynab_mcp.templates.prompts")
REVIEW_SPENDING_TEMPLATE = _templates.joinpath(
    "review-monthly-spending.md",
).read_text(encoding="utf-8")
ENTER_TRANSACTIONS_TEMPLATE = _templates.joinpath(
    "enter-transactions.md",
).read_text(encoding="utf-8")
BUDGET_HEALTH_TEMPLATE = _templates.joinpath(
    "budget-health-check.md",
).read_text(encoding="utf-8")


def _resource_uri(budget_id: str, resource: str) -> str:
    """Build a ynab:// resource URI.

    Args:
        budget_id: The YNAB budget ID.
        resource: The resource path suffix.

    Returns:
        The full resource URI string.
    """
    return f"{_RESOURCE_BASE}/{budget_id}/{resource}"


def _resolve_step() -> str:
    """Return instruction to resolve budget via manage_budgets.

    Returns:
        Step text instructing LLM to resolve the budget ID.
    """
    return '1. Use the `manage_budgets` tool with action="list" to find the budget ID.'


@mcp.prompt()
def review_monthly_spending(
    month: str,
    budget_id: str | None = None,
) -> str:
    """Guide the LLM through reviewing a month's spending.

    Produces a step-by-step workflow that reads budget context
    via MCP resources, then uses tools to analyze spending.

    Args:
        month: The month to review (YYYY-MM format).
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for monthly spending review.
    """
    if budget_id:
        return REVIEW_SPENDING_TEMPLATE.format(budget_id=budget_id, month=month)

    resolve = _resolve_step()
    body = REVIEW_SPENDING_TEMPLATE.format(budget_id="{budget_id}", month=month)
    # Insert resolve step after the header line
    lines = body.split("\n")
    header = lines[0]
    # Renumber steps: existing steps start at 1, shift to start at 2
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
def enter_transactions(budget_id: str | None = None) -> str:
    """Guide the LLM through entering transactions.

    Produces a step-by-step workflow that reads account and category
    context, then walks through transaction entry.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for transaction entry.
    """
    if budget_id:
        return ENTER_TRANSACTIONS_TEMPLATE.format(budget_id=budget_id)

    resolve = _resolve_step()
    body = ENTER_TRANSACTIONS_TEMPLATE.format(budget_id="{budget_id}")
    lines = body.split("\n")
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
def budget_health_check(budget_id: str | None = None) -> str:
    """Guide the LLM through a budget health review.

    Produces a step-by-step workflow that reads account and category
    data, then analyzes overall budget health.

    Args:
        budget_id: Optional budget ID. If not provided, the LLM
            will be instructed to resolve it first.

    Returns:
        Guided workflow text for budget health review.
    """
    if budget_id:
        return BUDGET_HEALTH_TEMPLATE.format(budget_id=budget_id)

    resolve = _resolve_step()
    body = BUDGET_HEALTH_TEMPLATE.format(budget_id="{budget_id}")
    lines = body.split("\n")
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
