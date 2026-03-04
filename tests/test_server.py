"""Tests for FastMCP server lifespan and startup validation."""

import ast
import inspect

import pytest

from ynab_mcp.client import YNABClient
from ynab_mcp.server import AppContext, lifespan


class TestLifespanStartup:
    """Tests for server lifespan startup behavior."""

    @pytest.mark.anyio
    async def test_missing_pat_raises_runtime_error(self, monkeypatch):
        """Missing YNAB_PAT env var causes startup failure."""
        monkeypatch.delenv("YNAB_PAT", raising=False)
        mock_server = None  # lifespan should fail before using this

        with pytest.raises(RuntimeError, match="YNAB_PAT"):
            async with lifespan(mock_server):
                pass

    @pytest.mark.anyio
    async def test_invalid_pat_raises_on_validation(self, monkeypatch, mocker):
        """Invalid PAT (validate_token fails) causes startup failure."""
        monkeypatch.setenv("YNAB_PAT", "invalid-token")

        mock_http_cls = mocker.patch("ynab_mcp.server.httpx.AsyncClient")
        mock_http_instance = mocker.AsyncMock()
        mock_http_cls.return_value.__aenter__ = mocker.AsyncMock(
            return_value=mock_http_instance,
        )
        mock_http_cls.return_value.__aexit__ = mocker.AsyncMock(return_value=False)

        mocker.patch.object(
            YNABClient,
            "validate_token",
            side_effect=RuntimeError("auth failed"),
        )

        with pytest.raises(RuntimeError, match="auth failed"):
            async with lifespan(mocker.AsyncMock()):
                pass

    @pytest.mark.anyio
    async def test_valid_pat_yields_app_context(self, monkeypatch, mocker):
        """Valid PAT allows lifespan to complete and yield AppContext."""
        monkeypatch.setenv("YNAB_PAT", "valid-token-123")

        mock_http_cls = mocker.patch("ynab_mcp.server.httpx.AsyncClient")
        mock_http_instance = mocker.AsyncMock()
        mock_http_cls.return_value.__aenter__ = mocker.AsyncMock(
            return_value=mock_http_instance,
        )
        mock_http_cls.return_value.__aexit__ = mocker.AsyncMock(return_value=False)

        mocker.patch.object(
            YNABClient,
            "validate_token",
            return_value="user-id-abc",
        )

        async with lifespan(mocker.AsyncMock()) as ctx:
            assert isinstance(ctx, AppContext)

    @pytest.mark.anyio
    async def test_app_context_client_is_ynab_client(self, monkeypatch, mocker):
        """AppContext.client is a YNABClient instance."""
        monkeypatch.setenv("YNAB_PAT", "valid-token-123")

        mock_http_cls = mocker.patch("ynab_mcp.server.httpx.AsyncClient")
        mock_http_instance = mocker.AsyncMock()
        mock_http_cls.return_value.__aenter__ = mocker.AsyncMock(
            return_value=mock_http_instance,
        )
        mock_http_cls.return_value.__aexit__ = mocker.AsyncMock(return_value=False)

        mocker.patch.object(
            YNABClient,
            "validate_token",
            return_value="user-id-abc",
        )

        async with lifespan(mocker.AsyncMock()) as ctx:
            assert isinstance(ctx.client, YNABClient)


class TestServerCompliance:
    """Tests for server code quality and compliance."""

    def test_no_print_calls_in_server_source(self):
        """server.py must not use print() (stdout is MCP transport)."""
        source = inspect.getsource(
            __import__("ynab_mcp.server", fromlist=["server"]),
        )
        tree = ast.parse(source)
        print_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ]
        assert print_calls == [], "server.py must not call print()"

    def test_logging_configured_to_stderr(self):
        """Logging basicConfig uses stderr, not stdout."""
        source = inspect.getsource(
            __import__("ynab_mcp.server", fromlist=["server"]),
        )
        # Verify logging is configured to stderr in source
        assert "stream=sys.stderr" in source, (
            "server.py must configure logging to stderr"
        )
        # Verify stdout is never used for logging
        assert "stream=sys.stdout" not in source
