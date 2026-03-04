"""FastMCP server for YNAB with lifespan-managed dependencies.

Provides the MCP server instance with:
- Lifespan-managed httpx client (created once, closed on shutdown)
- PAT validation at startup (fast-fail on bad auth)
- AppContext dataclass for sharing dependencies across tools
- Logging configured to stderr (stdout is MCP transport)
"""

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastmcp import Context, FastMCP

from ynab_mcp.client import YNABClient
from ynab_mcp.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


@dataclass
class AppContext:
    """Shared dependencies for all MCP tools.

    Created during server lifespan and available to tools via
    ``ctx.lifespan_context``.

    Attributes:
        client: The YNAB API client instance.
    """

    client: YNABClient


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage server lifecycle: create client, validate auth, cleanup.

    Creates an httpx AsyncClient with YNAB base URL and Bearer auth,
    wraps it in a YNABClient with a RateLimiter, validates the PAT
    by calling GET /user, then yields the AppContext for tools.

    On exit, the httpx client is closed.

    Args:
        _server: The FastMCP server instance (required by protocol).

    Yields:
        AppContext with the authenticated YNAB client.

    Raises:
        RuntimeError: If YNAB_PAT environment variable is not set
            or if PAT validation fails.
    """
    token = os.environ.get("YNAB_PAT")
    if not token:
        logger.error("YNAB_PAT environment variable is not set")
        msg = (
            "YNAB_PAT environment variable is required. "
            "Set it to your YNAB Personal Access Token."
        )
        raise RuntimeError(msg)

    async with httpx.AsyncClient(
        base_url="https://api.ynab.com/v1",
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0),
    ) as http_client:
        rate_limiter = RateLimiter()
        client = YNABClient(http_client, rate_limiter)

        user_id = await client.validate_token()
        logger.info("Authenticated as user %s", user_id)

        yield AppContext(client=client)


mcp = FastMCP("YNAB", lifespan=lifespan)


@mcp.tool
async def list_budgets(ctx: Context) -> str:
    """List all available YNAB budgets.

    Returns a formatted list of budget names and IDs, or a message
    if no budgets are found.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        A newline-separated list of budgets with names and IDs.
    """
    app: AppContext = ctx.lifespan_context
    data = await app.client.get("/budgets")
    budgets = data["budgets"]
    lines = [f"- {b['name']} (ID: {b['id']})" for b in budgets]
    return "\n".join(lines) if lines else "No budgets found."


if __name__ == "__main__":
    mcp.run()
