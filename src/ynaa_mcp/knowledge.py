"""MCP Resource definitions for YNAB methodology knowledge.

Exposes static YNAB budgeting knowledge as MCP Resources at
``ynab://knowledge/`` URIs. LLMs can read these resources to
understand YNAB methodology without hallucinating concepts.

All resources return markdown content loaded at import time
from the ``methodology/`` subpackage.
"""

from importlib import resources as pkg_resources

from ynaa_mcp.app import mcp


_methodology = pkg_resources.files("ynaa_mcp.methodology")

TERMINOLOGY_CONTENT = _methodology.joinpath("terminology.md").read_text(
    encoding="utf-8",
)
CREDIT_CARDS_CONTENT = _methodology.joinpath("credit-cards.md").read_text(
    encoding="utf-8",
)
GOALS_CONTENT = _methodology.joinpath("goals.md").read_text(encoding="utf-8")
OVERSPENDING_CONTENT = _methodology.joinpath("overspending.md").read_text(
    encoding="utf-8",
)
RECONCILIATION_CONTENT = _methodology.joinpath("reconciliation.md").read_text(
    encoding="utf-8",
)


@mcp.resource("ynab://knowledge/terminology", mime_type="text/markdown")
def terminology() -> str:
    """YNAB terminology and key concepts reference.

    Covers milliunits, on-budget vs off-budget accounts,
    age of money, To Be Budgeted, the Four Rules, and
    transaction states.

    Returns:
        Markdown content explaining YNAB terminology.
    """
    return TERMINOLOGY_CONTENT


@mcp.resource("ynab://knowledge/credit-cards", mime_type="text/markdown")
def credit_cards() -> str:
    """YNAB credit card handling guide.

    Covers the Credit Card Payment category, budgeting for
    purchases on credit, making payments, returns and refunds,
    pre-YNAB debt, and common mistakes.

    Returns:
        Markdown content explaining credit card handling in YNAB.
    """
    return CREDIT_CARDS_CONTENT


@mcp.resource("ynab://knowledge/goals", mime_type="text/markdown")
def goals() -> str:
    """YNAB goal types reference.

    Covers Target Category Balance, Monthly Savings Builder,
    Needed for Spending goal types with API field mappings
    and use case guidance.

    Returns:
        Markdown content explaining YNAB goal types.
    """
    return GOALS_CONTENT


@mcp.resource("ynab://knowledge/overspending", mime_type="text/markdown")
def overspending() -> str:
    """YNAB overspending behavior guide.

    Covers cash vs credit overspending, negative balance
    rollover behavior, and strategies for handling
    overspent categories.

    Returns:
        Markdown content explaining overspending in YNAB.
    """
    return OVERSPENDING_CONTENT


@mcp.resource("ynab://knowledge/reconciliation", mime_type="text/markdown")
def reconciliation() -> str:
    """YNAB reconciliation process guide.

    Covers the step-by-step reconciliation process,
    transaction statuses, adjustment transactions,
    and best practices for regular reconciliation.

    Returns:
        Markdown content explaining reconciliation in YNAB.
    """
    return RECONCILIATION_CONTENT
