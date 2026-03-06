"""YNAB API error types and structured error formatting.

Provides a custom exception for YNAB API errors and a formatting function
that produces user-friendly messages suitable for MCP ToolError responses.
Error messages differentiate between user errors (4xx -- guide correction)
and server errors (5xx -- clarify not user's fault), with retry hints for
transient failures (429, 5xx).
"""

from http import HTTPStatus


_NOT_FOUND = HTTPStatus.NOT_FOUND
_TOO_MANY_REQUESTS = HTTPStatus.TOO_MANY_REQUESTS
_INTERNAL_SERVER_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR


class YNABAPIError(Exception):
    """Raised when the YNAB API returns an error response.

    Attributes:
        status_code: HTTP status code from the YNAB API.
        error_id: YNAB-specific error identifier (e.g., "404.2").
        name: YNAB error name (e.g., "resource_not_found").
        detail: Human-readable error description from YNAB.
    """

    def __init__(
        self,
        status_code: int,
        error_id: str,
        name: str,
        detail: str,
    ) -> None:
        """Initialize a YNABAPIError.

        Args:
            status_code: HTTP status code from the YNAB API.
            error_id: YNAB-specific error identifier.
            name: YNAB error name.
            detail: Human-readable error description.
        """
        super().__init__(detail)
        self.status_code = status_code
        self.error_id = error_id
        self.name = name
        self.detail = detail


def format_error(error: YNABAPIError) -> str:
    """Format a YNAB API error into a user-friendly message string.

    The returned string is suitable for passing to FastMCP's ToolError
    constructor. Messages include the original YNAB error name in
    parentheses for debugging.

    Message tone varies by error category:
        - 404: Guide user to check their input (resource ID).
        - 429: Explain rate limit and suggest retry timing.
        - 5xx: Clarify the error is not the user's fault; suggest retry.
        - Other 4xx: Direct message guiding user to correct their input.

    Args:
        error: The YNAB API error to format.

    Returns:
        A formatted error message string.
    """
    if error.status_code == _NOT_FOUND:
        return (
            f"Resource not found: {error.detail} ({error.name}). "
            f"Check that the ID is correct."
        )

    if error.status_code == _TOO_MANY_REQUESTS:
        return (
            f"Rate limit reached. YNAB allows 200 requests/hour. "
            f"Try again in a few minutes. ({error.name})"
        )

    if error.status_code >= _INTERNAL_SERVER_ERROR:
        return (
            f"YNAB server error (not your fault): {error.detail} ({error.name}). "
            f"This is usually temporary -- try again shortly."
        )

    return f"{error.detail} ({error.name})"
