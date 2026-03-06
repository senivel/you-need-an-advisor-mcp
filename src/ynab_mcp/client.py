"""YNAB API client wrapping httpx with auth, rate limiting, and conversion.

Provides ``YNABClient``, the single point of contact with the YNAB API.
All requests go through this client, which handles:

- Rate limit checking before each request
- Bearer token authentication via the injected httpx client
- YNAB error response parsing into ``YNABAPIError``
- Data envelope unwrapping (``response["data"]``)
- Milliunit-to-dollar conversion on response fields
- Delta request caching for supported endpoints
"""

import logging
from http import HTTPStatus
from typing import Any, cast

import httpx
from fastmcp.exceptions import ToolError

from ynab_mcp.cache import CacheStore, cache_key_from_path, strip_server_knowledge
from ynab_mcp.converters import milliunits_to_dollars
from ynab_mcp.errors import YNABAPIError
from ynab_mcp.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)

_OK = HTTPStatus.OK

# JSON response types -- Any is unavoidable for recursive JSON processing
type JSONValue = dict[str, Any] | list[Any] | str | int | float | bool | None

MILLIUNIT_FIELDS: frozenset[str] = frozenset({
    "balance",
    "cleared_balance",
    "uncleared_balance",
    "budgeted",
    "activity",
    "amount",
    "goal_target",
    "goal_overall_left",
    "goal_under_funded",
    "allocation",
    "spent",
    "income",
    "to_be_budgeted",
})
"""Field names that contain milliunit values in YNAB API responses."""


def _is_milliunit_field(key: str) -> bool:
    """Check whether a response field name contains milliunit values.

    Matches exact field names in :data:`MILLIUNIT_FIELDS` plus any key
    ending with ``_balance`` or ``_amount`` for forward compatibility.

    Args:
        key: The field name to check.

    Returns:
        True if the field contains milliunit values.
    """
    if key in MILLIUNIT_FIELDS:
        return True
    return key.endswith(("_balance", "_amount"))


class YNABClient:
    """Async client for the YNAB API with rate limiting and conversion.

    Accepts an injected ``httpx.AsyncClient`` (created during server lifespan)
    and a ``RateLimiter``. Does NOT create its own HTTP client.

    Attributes:
        _http: The injected httpx async client.
        _rate_limiter: The rate limiter instance.
        _cache: Optional delta cache store for reducing API calls.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        rate_limiter: RateLimiter,
        *,
        cache: CacheStore | None = None,
    ) -> None:
        """Initialize the YNAB client with injected dependencies.

        Args:
            http_client: An httpx.AsyncClient pre-configured with base URL
                and authorization headers.
            rate_limiter: A RateLimiter instance for tracking API usage.
            cache: Optional CacheStore for delta request caching.
        """
        self._http = http_client
        self._rate_limiter = rate_limiter
        self._cache = cache

    async def validate_token(self) -> str:
        """Validate the YNAB personal access token by calling GET /user.

        Returns:
            The authenticated user's ID string.
        """
        data = await self.request("GET", "/user")
        user_info: dict[str, Any] = data["user"]
        return user_info["id"]

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any]:
        """Send a request to the YNAB API with rate limiting and conversion.

        Steps:
            1. Check rate limiter -- raise ToolError if denied
            2. Send HTTP request
            3. Record timestamp in rate limiter
            4. Parse error responses into YNABAPIError
            5. Unwrap the ``data`` envelope
            6. Convert milliunit fields to dollars

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API path relative to base URL (e.g., ``/user``).
            **kwargs: Additional keyword arguments passed to httpx
                (Any required -- httpx accepts diverse parameter types).

        Returns:
            The unwrapped ``data`` dict from the YNAB response with
            milliunit fields converted to dollar amounts.

        Raises:
            ToolError: If the rate limiter denies the request.
        """
        allowed, count, retry_after = self._rate_limiter.check()
        if not allowed:
            retry_seconds = int(retry_after) if retry_after is not None else 60
            logger.warning(
                "Rate limit reached: %d requests in window, retry after %ds",
                count,
                retry_seconds,
            )
            msg = (
                f"Rate limit reached ({count} requests this hour). "
                f"Try again in {retry_seconds} seconds."
            )
            raise ToolError(msg)

        response: httpx.Response = await self._http.request(method, path, **kwargs)
        self._rate_limiter.record()

        if response.status_code >= _OK.real + 100:
            self._raise_api_error(response)

        json_data: dict[str, Any] = response.json()
        data: dict[str, Any] = json_data["data"]
        converted = cast("dict[str, Any]", self._convert_milliunits(data))

        if method != "GET" and self._cache:
            self._cache.invalidate_for_mutation(path)

        return converted

    async def get(self, path: str, **kwargs: JSONValue) -> dict[str, Any]:
        """Send a GET request, using delta cache when available.

        For delta-capable endpoints, injects ``last_knowledge_of_server``
        when cached knowledge exists, and merges delta responses into the
        cache. Strips ``server_knowledge`` from returned data.

        Args:
            path: API path relative to base URL.
            **kwargs: Additional keyword arguments passed to httpx.

        Returns:
            The unwrapped and converted response data, with
            ``server_knowledge`` stripped if present.
        """
        cache_key = cache_key_from_path(path) if self._cache else None

        if cache_key and self._cache:
            knowledge = self._cache.get_knowledge(cache_key)
            if knowledge is not None:
                existing_params = kwargs.get("params")
                params: dict[str, Any] = (
                    dict(cast("dict[str, Any]", existing_params))
                    if existing_params
                    else {}
                )
                params["last_knowledge_of_server"] = knowledge
                kwargs["params"] = params

        data = await self.request("GET", path, **kwargs)

        if cache_key and self._cache and "server_knowledge" in data:
            sk = data["server_knowledge"]
            if self._cache.get_cached_data(cache_key) is not None:
                self._cache.merge_delta(cache_key, sk, strip_server_knowledge(data))
            else:
                self._cache.update(cache_key, sk, strip_server_knowledge(data))
            return strip_server_knowledge(data)

        return data

    async def post(self, path: str, **kwargs: JSONValue) -> dict[str, Any]:
        """Send a POST request to the YNAB API.

        Args:
            path: API path relative to base URL.
            **kwargs: Additional keyword arguments passed to httpx.

        Returns:
            The unwrapped and converted response data.
        """
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: JSONValue) -> dict[str, Any]:
        """Send a PUT request to the YNAB API.

        Args:
            path: API path relative to base URL.
            **kwargs: Additional keyword arguments passed to httpx.

        Returns:
            The unwrapped and converted response data.
        """
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs: JSONValue) -> dict[str, Any]:
        """Send a DELETE request to the YNAB API.

        Args:
            path: API path relative to base URL.
            **kwargs: Additional keyword arguments passed to httpx.

        Returns:
            The unwrapped and converted response data.
        """
        return await self.request("DELETE", path, **kwargs)

    async def patch(self, path: str, **kwargs: JSONValue) -> dict[str, Any]:
        """Send a PATCH request to the YNAB API.

        Args:
            path: API path relative to base URL.
            **kwargs: Additional keyword arguments passed to httpx.

        Returns:
            The unwrapped and converted response data.
        """
        return await self.request("PATCH", path, **kwargs)

    @staticmethod
    def _raise_api_error(response: httpx.Response) -> None:
        """Parse a YNAB error response and raise YNABAPIError.

        Args:
            response: The httpx response with a non-2xx status code.

        Raises:
            YNABAPIError: Always raised with parsed error details.
        """
        error_data = response.json().get("error", {})
        raise YNABAPIError(
            status_code=response.status_code,
            error_id=error_data.get("id", "unknown"),
            name=error_data.get("name", "unknown"),
            detail=error_data.get("detail", "Unknown error"),
        )

    def _convert_milliunits(self, data: JSONValue) -> JSONValue:
        """Recursively convert milliunit fields to dollar amounts.

        Walks the response data structure. For any key matching a known
        milliunit field name, replaces the integer value with a float
        dollar amount via ``milliunits_to_dollars()``.

        Args:
            data: A dict, list, or primitive value from the YNAB response.

        Returns:
            The same structure with milliunit integers replaced by
            dollar floats.
        """
        if isinstance(data, dict):
            return {
                key: self._convert_milliunit_value(key, value)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [self._convert_milliunits(item) for item in data]
        return data

    def _convert_milliunit_value(self, key: str, value: JSONValue) -> JSONValue:
        """Convert a single value if its key is a milliunit field.

        Args:
            key: The field name.
            value: The field value.

        Returns:
            The converted dollar amount if applicable, otherwise
            the recursively processed value.
        """
        if value is None:
            return None
        if _is_milliunit_field(key) and isinstance(value, int):
            return milliunits_to_dollars(value)
        return self._convert_milliunits(value)
