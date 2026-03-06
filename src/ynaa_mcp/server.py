"""MCP server wiring: imports tool/prompt/resource modules to register handlers."""

# Side-effect imports: each module registers MCP handlers at import time.
import ynaa_mcp.analysis  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.knowledge  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.prompts  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.resources  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.tools.accounts  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.tools.budgets  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.tools.cache  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.tools.categories  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.tools.months  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.tools.payees  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.tools.scheduled  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.tools.transactions  # pyright: ignore[reportUnusedImport]
import ynaa_mcp.workflows  # pyright: ignore[reportUnusedImport]
from ynaa_mcp.app import AppContext, lifespan, mcp


__all__ = ["AppContext", "lifespan", "mcp"]
