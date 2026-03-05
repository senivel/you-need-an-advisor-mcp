"""MCP Prompt templates for common YNAB workflows.

Provides guided workflow instructions that help LLMs perform
multi-step YNAB tasks efficiently. Each prompt references the
specific MCP resources to read and tools to call.
"""

from ynab_mcp.server import mcp


_RESOURCE_BASE = "ynab://budgets"


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
    """Return instruction to resolve budget via list_budgets.

    Returns:
        Step text instructing LLM to resolve the budget ID.
    """
    return "1. Use the `list_budgets` tool to find the budget ID."


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
    steps: list[str] = []

    if budget_id:
        cat_uri = _resource_uri(budget_id, "categories")
    else:
        cat_uri = f"{_RESOURCE_BASE}/{{budget_id}}/categories"
        steps.append(_resolve_step())

    steps.extend([
        (
            f"Read the categories resource at `{cat_uri}` "
            "to understand the budget structure."
        ),
        (
            f'Use the `get_month_detail` tool with month="{month}" '
            "to see the month summary."
        ),
        (
            f'Use the `list_transactions` tool with month="{month}" '
            "to see all transactions for the month."
        ),
        (
            "Summarize spending by category, comparing "
            "budgeted amounts vs actual activity."
        ),
        ("Highlight any categories that are over budget (negative balance)."),
        (
            "Note the overall budget health: to-be-budgeted "
            "amount, total income vs total spending."
        ),
    ])

    numbered = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    return f"Review monthly spending for {month}.\n\n{numbered}"


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
    steps: list[str] = []

    if budget_id:
        acct_uri = _resource_uri(budget_id, "accounts")
        cat_uri = _resource_uri(budget_id, "categories")
    else:
        acct_uri = f"{_RESOURCE_BASE}/{{budget_id}}/accounts"
        cat_uri = f"{_RESOURCE_BASE}/{{budget_id}}/categories"
        steps.append(_resolve_step())

    steps.extend([
        (f"Read the accounts resource at `{acct_uri}` to know the available accounts."),
        (
            f"Read the categories resource at `{cat_uri}` "
            "to know the available categories."
        ),
        (
            "Ask the user for transaction details: date, "
            "payee, amount, account, category, and memo."
        ),
        "Use the `create_transaction` tool to enter each transaction.",
        "Confirm the transaction details after each entry.",
        "Ask if there are more transactions to enter.",
    ])

    numbered = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    return f"Enter transactions into the budget.\n\n{numbered}"


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
    steps: list[str] = []

    if budget_id:
        acct_uri = _resource_uri(budget_id, "accounts")
        cat_uri = _resource_uri(budget_id, "categories")
    else:
        acct_uri = f"{_RESOURCE_BASE}/{{budget_id}}/accounts"
        cat_uri = f"{_RESOURCE_BASE}/{{budget_id}}/categories"
        steps.append(_resolve_step())

    steps.extend([
        (
            f"Read the accounts resource at `{acct_uri}` "
            "to see current account balances."
        ),
        (f"Read the categories resource at `{cat_uri}` to see budget status."),
        "Use the `get_budget` tool for the budget-level summary.",
        (
            "Report on: total account balances, "
            "to-be-budgeted amount, overspent categories, "
            "and underfunded goals."
        ),
        "Suggest actionable next steps to improve budget health.",
    ])

    numbered = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    return f"Perform a budget health check.\n\n{numbered}"
