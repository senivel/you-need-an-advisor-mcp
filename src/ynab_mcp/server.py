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

from ynab_mcp.budget_resolver import resolve_budget
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

    Returns a count header followed by a structured list of budget
    names, IDs, and last modified dates.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        Structured text with count header and budget details,
        or "No budgets found." if none exist.
    """
    app: AppContext = ctx.lifespan_context
    data = await app.client.get("/budgets")
    budgets = data["budgets"]

    if not budgets:
        return "No budgets found."

    lines = [f"{len(budgets)} budgets found:"]
    for b in budgets:
        lines.extend((
            f"- {b['name']}",
            f"  ID: {b['id']}",
            f"  Last modified: {b['last_modified_on']}",
        ))
    return "\n".join(lines)


@mcp.tool
async def get_budget(
    ctx: Context,
    budget_id_or_name: str | None = None,
) -> str:
    """Get detailed information about a YNAB budget.

    Fetches budget details and settings (date format, currency format)
    in a single response. Uses budget resolution to find the budget
    by UUID or fuzzy name match.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Auto-resolves if only
            one budget exists.

    Returns:
        Structured text with budget name, months, date format, and
        currency format.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, info = await resolve_budget(app.client, budget_id_or_name)

    data = await app.client.get(f"/budgets/{budget_id}")
    budget = data["budget"]

    settings_data = await app.client.get(f"/budgets/{budget_id}/settings")
    settings = settings_data["settings"]

    date_fmt = settings.get("date_format", {}).get("format", "N/A")
    currency = settings.get("currency_format", {}).get("iso_code", "N/A")

    lines = [
        f"Budget: {budget['name']}",
        f"  ID: {budget['id']}",
        f"  First month: {budget['first_month']}",
        f"  Last month: {budget['last_month']}",
        f"  Date format: {date_fmt}",
        f"  Currency: {currency}",
    ]
    result = "\n".join(lines)

    if info:
        result = f"{info}\n\n{result}"
    return result


@mcp.tool
async def get_user(ctx: Context) -> str:
    """Get the authenticated YNAB user's information.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.

    Returns:
        Structured text with the user ID.
    """
    app: AppContext = ctx.lifespan_context
    data = await app.client.get("/user")
    user = data["user"]
    return f"User ID: {user['id']}"


if __name__ == "__main__":
    mcp.run()
