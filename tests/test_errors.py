"""Tests for YNAB error handling and formatting."""

from ynab_mcp.errors import YNABAPIError, format_error


class TestYNABAPIError:
    """Tests for YNABAPIError exception class."""

    def test_stores_status_code(self):
        error = YNABAPIError(
            status_code=404,
            error_id="404.2",
            name="resource_not_found",
            detail="Budget not found",
        )
        assert error.status_code == 404

    def test_stores_error_id(self):
        error = YNABAPIError(
            status_code=404,
            error_id="404.2",
            name="resource_not_found",
            detail="Budget not found",
        )
        assert error.error_id == "404.2"

    def test_stores_name(self):
        error = YNABAPIError(
            status_code=404,
            error_id="404.2",
            name="resource_not_found",
            detail="Budget not found",
        )
        assert error.name == "resource_not_found"

    def test_stores_detail(self):
        error = YNABAPIError(
            status_code=404,
            error_id="404.2",
            name="resource_not_found",
            detail="Budget not found",
        )
        assert error.detail == "Budget not found"

    def test_is_exception(self):
        error = YNABAPIError(
            status_code=404,
            error_id="404.2",
            name="resource_not_found",
            detail="Budget not found",
        )
        assert isinstance(error, Exception)


class TestFormatError:
    """Tests for format_error function."""

    def test_404_produces_resource_not_found_message(self):
        error = YNABAPIError(
            status_code=404,
            error_id="404.2",
            name="resource_not_found",
            detail="Budget not found",
        )
        result = format_error(error)
        assert result == (
            "Resource not found: Budget not found (resource_not_found). "
            "Check that the ID is correct."
        )

    def test_429_produces_rate_limit_message_with_retry_hint(self):
        error = YNABAPIError(
            status_code=429,
            error_id="429",
            name="too_many_requests",
            detail="Too many requests",
        )
        result = format_error(error)
        assert "Rate limit reached" in result
        assert "200 requests/hour" in result
        assert "Try again" in result
        assert "(too_many_requests)" in result

    def test_5xx_produces_server_error_message_with_retry_hint(self):
        error = YNABAPIError(
            status_code=500,
            error_id="500",
            name="internal_server_error",
            detail="Internal server error",
        )
        result = format_error(error)
        assert "not your fault" in result
        assert "try again" in result.lower()
        assert "(internal_server_error)" in result

    def test_503_also_produces_server_error_message(self):
        error = YNABAPIError(
            status_code=503,
            error_id="503",
            name="service_unavailable",
            detail="Service unavailable",
        )
        result = format_error(error)
        assert "not your fault" in result
        assert "try again" in result.lower()

    def test_400_user_error_produces_detail_with_name(self):
        error = YNABAPIError(
            status_code=400,
            error_id="400",
            name="bad_request",
            detail="Invalid amount format",
        )
        result = format_error(error)
        assert result == "Invalid amount format (bad_request)"

    def test_user_errors_guide_correction_not_blame_server(self):
        """User errors (4xx) should not say 'not your fault'."""
        error = YNABAPIError(
            status_code=400,
            error_id="400",
            name="bad_request",
            detail="Invalid amount format",
        )
        result = format_error(error)
        assert "not your fault" not in result

    def test_api_errors_clarify_not_users_fault(self):
        """API errors (5xx) should clarify it's not the user's fault."""
        error = YNABAPIError(
            status_code=502,
            error_id="502",
            name="bad_gateway",
            detail="Bad gateway",
        )
        result = format_error(error)
        assert "not your fault" in result

    def test_format_error_returns_string(self):
        """format_error should return a string, not raise."""
        error = YNABAPIError(
            status_code=404,
            error_id="404.2",
            name="resource_not_found",
            detail="Budget not found",
        )
        result = format_error(error)
        assert isinstance(result, str)
