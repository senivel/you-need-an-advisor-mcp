"""Core MCP application: FastMCP instance, AppContext, and lifespan management.

Provides the foundational server infrastructure that tool modules import
from. This module owns the single FastMCP instance and must NOT import
from tools/, prompts.py, or resources.py (one-way dependency arrow).
"""

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastmcp import FastMCP

from ynaa_mcp.cache import CacheStore
from ynaa_mcp.client import YNABClient
from ynaa_mcp.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


@dataclass
class AppContext:
    """Shared dependencies for all MCP tools.

    Created during server lifespan and available to tools via
    ``ctx.lifespan_context``.

    Attributes:
        client: The YNAB API client instance.
        cache: The delta cache store for YNAB API responses.
    """

    client: YNABClient
    cache: CacheStore


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
        cache = CacheStore()
        client = YNABClient(http_client, rate_limiter, cache=cache)

        user_id = await client.validate_token()
        logger.info("Authenticated as user %s", user_id)

        yield AppContext(client=client, cache=cache)


mcp = FastMCP("YNAB", lifespan=lifespan)
