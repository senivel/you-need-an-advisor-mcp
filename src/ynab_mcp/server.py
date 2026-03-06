"""MCP server wiring: imports tool/prompt/resource modules to register handlers."""

# Side-effect imports: each module registers MCP handlers at import time.
import ynab_mcp.analysis  # pyright: ignore[reportUnusedImport]
import ynab_mcp.knowledge  # pyright: ignore[reportUnusedImport]
import ynab_mcp.prompts  # pyright: ignore[reportUnusedImport]
import ynab_mcp.resources  # pyright: ignore[reportUnusedImport]
import ynab_mcp.tools.accounts  # pyright: ignore[reportUnusedImport]
import ynab_mcp.tools.budgets  # pyright: ignore[reportUnusedImport]
import ynab_mcp.tools.cache  # pyright: ignore[reportUnusedImport]
import ynab_mcp.tools.categories  # pyright: ignore[reportUnusedImport]
import ynab_mcp.tools.months  # pyright: ignore[reportUnusedImport]
import ynab_mcp.tools.payees  # pyright: ignore[reportUnusedImport]
import ynab_mcp.tools.scheduled  # pyright: ignore[reportUnusedImport]
import ynab_mcp.tools.transactions  # pyright: ignore[reportUnusedImport]
from ynab_mcp.app import AppContext, lifespan, mcp


__all__ = ["AppContext", "lifespan", "mcp"]
