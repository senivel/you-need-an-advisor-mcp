"""Pydantic models for YNAB API responses.

Base models for validating and typing YNAB API response data.
All models use ``extra="ignore"`` so that additional fields returned
by the YNAB API do not cause validation errors.
"""

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """A single YNAB API error detail.

    Attributes:
        id: YNAB error identifier (e.g., "404.2").
        name: Error name (e.g., "resource_not_found").
        detail: Human-readable error description.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    detail: str


class ErrorResponse(BaseModel):
    """Top-level YNAB API error response wrapper.

    Attributes:
        error: The error detail object.
    """

    model_config = ConfigDict(extra="ignore")

    error: ErrorDetail


class BudgetSummary(BaseModel):
    """Summary of a single YNAB budget.

    Attributes:
        id: Budget UUID.
        name: Budget display name.
        last_modified_on: ISO 8601 timestamp of last modification.
        first_month: First month in the budget (YYYY-MM-DD).
        last_month: Last month in the budget (YYYY-MM-DD).
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    last_modified_on: str
    first_month: str
    last_month: str


class BudgetsResponse(BaseModel):
    """Response wrapper for the GET /budgets endpoint.

    Attributes:
        budgets: List of budget summaries.
    """

    model_config = ConfigDict(extra="ignore")

    budgets: list[BudgetSummary]


class UserResponse(BaseModel):
    """Response for the GET /user endpoint.

    Attributes:
        id: User UUID.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
