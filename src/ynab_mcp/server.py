"""MCP server wiring: imports tool/prompt/resource modules to register handlers."""

import ynab_mcp.prompts
import ynab_mcp.resources
import ynab_mcp.tools.accounts
import ynab_mcp.tools.budgets
import ynab_mcp.tools.cache
import ynab_mcp.tools.categories
import ynab_mcp.tools.months
import ynab_mcp.tools.payees
import ynab_mcp.tools.scheduled
import ynab_mcp.tools.transactions
from ynab_mcp.app import AppContext, lifespan, mcp


__all__ = ["AppContext", "lifespan", "mcp"]
