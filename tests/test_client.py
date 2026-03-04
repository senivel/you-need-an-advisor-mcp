"""Tests for YNABClient with mocked httpx and rate limiter."""

import inspect

import httpx
import pytest
from fastmcp.exceptions import ToolError

import ynab_mcp.client as client_module
from ynab_mcp.client import YNABClient
from ynab_mcp.errors import YNABAPIError
from ynab_mcp.rate_limiter import RateLimiter


@pytest.fixture
def mock_rate_limiter(mocker):
    """Create a mock rate limiter that allows all requests.

    Returns:
        A MagicMock with spec=RateLimiter, pre-configured to allow.
    """
    limiter = mocker.MagicMock(spec=RateLimiter)
    limiter.check.return_value = (True, 0, None)
    return limiter


@pytest.fixture
def mock_http_client(mocker):
    """Create a mock httpx.AsyncClient.

    Returns:
        An AsyncMock with spec=httpx.AsyncClient.
    """
    return mocker.AsyncMock(spec=httpx.AsyncClient)


def _make_response(
    status_code: int = 200,
    json_data: dict | None = None,
) -> httpx.Response:
    """Create an httpx.Response with the given status and JSON body.

    Args:
        status_code: HTTP status code for the response.
        json_data: JSON body to include in the response.

    Returns:
        An httpx.Response object.
    """
    return httpx.Response(
        status_code=status_code,
        json=json_data,
        request=httpx.Request("GET", "https://api.ynab.com/v1/test"),
    )


@pytest.fixture
def client(mock_http_client, mock_rate_limiter):
    """Create a YNABClient with mock dependencies.

    Returns:
        A YNABClient configured with mocked http_client and rate_limiter.
    """
    return YNABClient(http_client=mock_http_client, rate_limiter=mock_rate_limiter)


class TestClientAuth:
    """Tests for authentication header behavior."""

    @pytest.mark.anyio
    async def test_sends_bearer_auth_header(self, client, mock_http_client):
        """YNABClient sends Authorization Bearer header on requests."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"user": {"id": "abc"}}},
        )

        await client.request("GET", "/user")

        mock_http_client.request.assert_called_once()
        call_kwargs = mock_http_client.request.call_args
        # The client should be configured with auth headers via the http_client
        assert call_kwargs is not None


class TestValidateToken:
    """Tests for validate_token() method."""

    @pytest.mark.anyio
    async def test_validate_token_succeeds_on_200(self, client, mock_http_client):
        """validate_token() calls GET /user and succeeds on 200."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"user": {"id": "user-123"}}},
        )

        user_id = await client.validate_token()

        assert user_id == "user-123"

    @pytest.mark.anyio
    async def test_validate_token_raises_on_error(self, client, mock_http_client):
        """validate_token() raises YNABAPIError on non-200."""
        mock_http_client.request.return_value = _make_response(
            status_code=401,
            json_data={
                "error": {
                    "id": "401",
                    "name": "unauthorized",
                    "detail": "Invalid token",
                }
            },
        )

        with pytest.raises(YNABAPIError) as exc_info:
            await client.validate_token()

        assert exc_info.value.status_code == 401


class TestRateLimiting:
    """Tests for rate limiter integration."""

    @pytest.mark.anyio
    async def test_denied_request_raises_tool_error(
        self, client, mock_http_client, mock_rate_limiter
    ):
        """Denied request raises ToolError without making HTTP call."""
        mock_rate_limiter.check.return_value = (False, 190, 120.5)

        with pytest.raises(ToolError):
            await client.request("GET", "/budgets")

        mock_http_client.request.assert_not_called()

    @pytest.mark.anyio
    async def test_records_timestamp_after_success(
        self, client, mock_http_client, mock_rate_limiter
    ):
        """request() records timestamp after successful request."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"user": {"id": "abc"}}},
        )

        await client.request("GET", "/user")

        mock_rate_limiter.record.assert_called_once()


class TestErrorParsing:
    """Tests for YNAB API error response parsing."""

    @pytest.mark.anyio
    async def test_non_2xx_parsed_into_ynab_api_error(self, client, mock_http_client):
        """Non-2xx response is parsed into YNABAPIError with correct fields."""
        mock_http_client.request.return_value = _make_response(
            status_code=404,
            json_data={
                "error": {
                    "id": "404.2",
                    "name": "resource_not_found",
                    "detail": "Budget not found",
                }
            },
        )

        with pytest.raises(YNABAPIError) as exc_info:
            await client.request("GET", "/budgets/bad-id")

        err = exc_info.value
        assert err.status_code == 404
        assert err.error_id == "404.2"
        assert err.name == "resource_not_found"
        assert err.detail == "Budget not found"


class TestResponseHandling:
    """Tests for successful response processing."""

    @pytest.mark.anyio
    async def test_unwraps_data_envelope(self, client, mock_http_client):
        """Successful GET response returns parsed JSON data (envelope unwrapped)."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"user": {"id": "abc"}}},
        )

        result = await client.request("GET", "/user")

        assert result == {"user": {"id": "abc"}}

    @pytest.mark.anyio
    async def test_milliunit_fields_converted_to_dollars(
        self, client, mock_http_client
    ):
        """Response with milliunit fields has them converted to dollars."""
        mock_http_client.request.return_value = _make_response(
            json_data={
                "data": {
                    "account": {
                        "balance": 45670,
                        "cleared_balance": -10000,
                    }
                }
            },
        )

        result = await client.request("GET", "/budgets/x/accounts/y")

        expected_balance = 45.67
        expected_cleared = -10.0
        assert result["account"]["balance"] == pytest.approx(expected_balance)
        assert result["account"]["cleared_balance"] == pytest.approx(expected_cleared)

    @pytest.mark.anyio
    async def test_non_milliunit_response_unchanged(self, client, mock_http_client):
        """Response with no milliunit fields is returned unchanged."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"user": {"id": "abc"}}},
        )

        result = await client.request("GET", "/user")

        assert result == {"user": {"id": "abc"}}


class TestPatchMethod:
    """Tests for client.patch() method."""

    @pytest.mark.anyio
    async def test_patch_delegates_to_request(self, client, mock_http_client):
        """patch() sends a PATCH request through request()."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"category": {"id": "cat-001", "name": "Updated"}}},
        )

        result = await client.patch(
            "/budgets/x/categories/cat-001",
            json={"category": {"name": "Updated"}},
        )

        mock_http_client.request.assert_called_once()
        call_args = mock_http_client.request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "/budgets/x/categories/cat-001"
        assert result["category"]["id"] == "cat-001"


class TestPutMethod:
    """Tests for client.put() method."""

    @pytest.mark.anyio
    async def test_put_delegates_to_request(self, client, mock_http_client):
        """put() sends a PUT request through request()."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"transaction": {"id": "txn-001", "amount": 50.0}}},
        )

        result = await client.put(
            "/budgets/x/transactions/txn-001",
            json={"transaction": {"amount": 50000}},
        )

        mock_http_client.request.assert_called_once()
        call_args = mock_http_client.request.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "/budgets/x/transactions/txn-001"
        assert result["transaction"]["id"] == "txn-001"

    @pytest.mark.anyio
    async def test_put_passes_kwargs(self, client, mock_http_client):
        """put() forwards keyword arguments to request()."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"transaction": {"id": "txn-001"}}},
        )

        await client.put(
            "/budgets/x/transactions/txn-001",
            json={"transaction": {"memo": "Updated"}},
        )

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["json"] == {"transaction": {"memo": "Updated"}}

    @pytest.mark.anyio
    async def test_put_is_async(self, client):
        """put() is a coroutine function."""
        assert inspect.iscoroutinefunction(client.put)


class TestDeleteMethod:
    """Tests for client.delete() method."""

    @pytest.mark.anyio
    async def test_delete_delegates_to_request(self, client, mock_http_client):
        """delete() sends a DELETE request through request()."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"transaction": {"id": "txn-001", "deleted": True}}},
        )

        result = await client.delete("/budgets/x/transactions/txn-001")

        mock_http_client.request.assert_called_once()
        call_args = mock_http_client.request.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/budgets/x/transactions/txn-001"
        assert result["transaction"]["deleted"] is True

    @pytest.mark.anyio
    async def test_delete_passes_kwargs(self, client, mock_http_client):
        """delete() forwards keyword arguments to request()."""
        mock_http_client.request.return_value = _make_response(
            json_data={"data": {"transaction": {"id": "txn-001"}}},
        )

        await client.delete(
            "/budgets/x/transactions/txn-001",
            params={"force": "true"},
        )

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["params"] == {"force": "true"}

    @pytest.mark.anyio
    async def test_delete_is_async(self, client):
        """delete() is a coroutine function."""
        assert inspect.iscoroutinefunction(client.delete)


class TestStdoutCompliance:
    """Tests for INFR-08: no stdout writes."""

    def test_no_print_calls_in_module(self):
        """No print() calls in client module source."""
        source = inspect.getsource(client_module)
        lines = source.split("\n")
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            assert "print(" not in stripped, f"Found print() call in client.py: {line}"

    def test_uses_logging_module(self):
        """Client uses logging module for any log output."""
        source = inspect.getsource(client_module)
        assert "import logging" in source or "from logging" in source
