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


class Account(BaseModel):
    """A YNAB account.

    Attributes:
        id: Account UUID.
        name: Account display name.
        type: Account type (checking, savings, etc.).
        on_budget: Whether account is on-budget.
        closed: Whether account is closed.
        balance: Current balance in dollars (converted from milliunits).
        cleared_balance: Cleared balance in dollars.
        uncleared_balance: Uncleared balance in dollars.
        note: Optional account note.
        transfer_payee_id: Payee ID for transfers to this account.
        deleted: Whether account is deleted.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    type: str
    on_budget: bool
    closed: bool
    balance: float
    cleared_balance: float
    uncleared_balance: float
    note: str | None = None
    transfer_payee_id: str | None = None
    deleted: bool


class Category(BaseModel):
    """A YNAB budget category.

    Attributes:
        id: Category UUID.
        category_group_id: Parent category group UUID.
        category_group_name: Parent category group name.
        name: Category display name.
        hidden: Whether category is hidden.
        budgeted: Budgeted amount in dollars.
        activity: Activity amount in dollars.
        balance: Balance in dollars.
        deleted: Whether category is deleted.
        note: Optional category note.
        goal_type: Goal type (TB, TBD, MF, NEED, DEBT).
        goal_target: Goal target amount in dollars.
        goal_target_month: Goal target month (YYYY-MM-DD).
        goal_percentage_complete: Goal completion percentage.
        goal_months_to_budget: Months remaining to reach goal.
        goal_under_funded: Amount under-funded in dollars.
        goal_overall_funded: Total funded toward goal in dollars.
        goal_overall_left: Amount remaining for goal in dollars.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    category_group_id: str
    category_group_name: str | None = None
    name: str
    hidden: bool
    budgeted: float
    activity: float
    balance: float
    deleted: bool
    note: str | None = None
    goal_type: str | None = None
    goal_target: float | None = None
    goal_target_month: str | None = None
    goal_percentage_complete: int | None = None
    goal_months_to_budget: int | None = None
    goal_under_funded: float | None = None
    goal_overall_funded: float | None = None
    goal_overall_left: float | None = None


class CategoryGroup(BaseModel):
    """A YNAB category group.

    Attributes:
        id: Category group UUID.
        name: Category group display name.
        hidden: Whether category group is hidden.
        deleted: Whether category group is deleted.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    hidden: bool
    deleted: bool


class CategoryGroupWithCategories(CategoryGroup):
    """A category group with its child categories.

    Attributes:
        categories: List of categories in this group.
    """

    categories: list[Category]


class UserResponse(BaseModel):
    """Response for the GET /user endpoint.

    Attributes:
        id: User UUID.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
