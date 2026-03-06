"""Shared fixtures for tool tests."""

import pytest


@pytest.fixture
def mock_ctx(mocker):
    """Create a mock MCP Context with a mocked YNABClient and CacheStore.

    Returns:
        A mock Context with lifespan_context.client and
        lifespan_context.cache set.
    """
    client = mocker.AsyncMock()
    cache = mocker.MagicMock()
    app = mocker.MagicMock()
    app.client = client
    app.cache = cache
    ctx = mocker.MagicMock()
    ctx.lifespan_context = app
    return ctx
