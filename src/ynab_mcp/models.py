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


class SubTransaction(BaseModel):
    """A YNAB sub-transaction (split transaction component).

    Attributes:
        id: Sub-transaction UUID.
        transaction_id: Parent transaction UUID.
        amount: Amount in dollars (converted from milliunits).
        deleted: Whether sub-transaction is deleted.
        payee_id: Payee UUID.
        payee_name: Payee display name.
        category_id: Category UUID.
        category_name: Category display name.
        memo: Optional memo text.
        transfer_account_id: Account UUID if this is a transfer.
        transfer_transaction_id: Matching transfer transaction UUID.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    transaction_id: str
    amount: float
    deleted: bool
    payee_id: str | None = None
    payee_name: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    memo: str | None = None
    transfer_account_id: str | None = None
    transfer_transaction_id: str | None = None


class TransactionDetail(BaseModel):
    """A detailed YNAB transaction.

    Attributes:
        id: Transaction UUID.
        date: Transaction date (YYYY-MM-DD).
        amount: Amount in dollars (converted from milliunits).
        account_id: Account UUID.
        account_name: Account display name.
        approved: Whether transaction is approved.
        cleared: Cleared status (cleared, uncleared, reconciled).
        deleted: Whether transaction is deleted.
        memo: Optional memo text.
        payee_id: Payee UUID.
        payee_name: Payee display name.
        category_id: Category UUID.
        category_name: Category display name.
        transfer_account_id: Account UUID if this is a transfer.
        transfer_transaction_id: Matching transfer transaction UUID.
        matched_transaction_id: Matched imported transaction UUID.
        import_id: Import identifier for deduplication.
        import_payee_name: Payee name from import source.
        import_payee_name_original: Original payee name from import source.
        flag_color: Transaction flag color.
        flag_name: Transaction flag name.
        debt_transaction_type: Debt transaction type (payment, etc.).
        subtransactions: List of sub-transactions (splits).
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    date: str
    amount: float
    account_id: str
    account_name: str
    approved: bool
    cleared: str
    deleted: bool
    memo: str | None = None
    payee_id: str | None = None
    payee_name: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    transfer_account_id: str | None = None
    transfer_transaction_id: str | None = None
    matched_transaction_id: str | None = None
    import_id: str | None = None
    import_payee_name: str | None = None
    import_payee_name_original: str | None = None
    flag_color: str | None = None
    flag_name: str | None = None
    debt_transaction_type: str | None = None
    subtransactions: list[SubTransaction] = []


class ScheduledSubTransaction(BaseModel):
    """A YNAB scheduled sub-transaction (split component).

    Attributes:
        id: Sub-transaction UUID.
        scheduled_transaction_id: Parent scheduled transaction UUID.
        amount: Amount in dollars (converted from milliunits).
        deleted: Whether sub-transaction is deleted.
        payee_id: Payee UUID.
        payee_name: Payee display name.
        category_id: Category UUID.
        category_name: Category display name.
        memo: Optional memo text.
        transfer_account_id: Account UUID if this is a transfer.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    scheduled_transaction_id: str
    amount: float
    deleted: bool
    payee_id: str | None = None
    payee_name: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    memo: str | None = None
    transfer_account_id: str | None = None


class ScheduledTransactionDetail(BaseModel):
    """A detailed YNAB scheduled transaction.

    Attributes:
        id: Scheduled transaction UUID.
        date_first: First occurrence date (YYYY-MM-DD).
        date_next: Next occurrence date (YYYY-MM-DD), None if completed.
        frequency: Recurrence frequency (never, daily, weekly, etc.).
        amount: Amount in dollars (converted from milliunits).
        account_id: Account UUID.
        account_name: Account display name.
        deleted: Whether scheduled transaction is deleted.
        payee_id: Payee UUID.
        payee_name: Payee display name.
        category_id: Category UUID.
        category_name: Category display name.
        memo: Optional memo text.
        flag_color: Flag color for the scheduled transaction.
        flag_name: Flag name for the scheduled transaction.
        transfer_account_id: Account UUID if this is a transfer.
        subtransactions: List of scheduled sub-transactions (splits).
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    date_first: str
    date_next: str | None = None
    frequency: str
    amount: float
    account_id: str
    account_name: str
    deleted: bool
    payee_id: str | None = None
    payee_name: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    memo: str | None = None
    flag_color: str | None = None
    flag_name: str | None = None
    transfer_account_id: str | None = None
    subtransactions: list[ScheduledSubTransaction] = []


class Payee(BaseModel):
    """A YNAB payee.

    Attributes:
        id: Payee UUID.
        name: Payee display name.
        transfer_account_id: Account UUID if this is a transfer payee.
        deleted: Whether payee is deleted.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    transfer_account_id: str | None = None
    deleted: bool


class PayeeLocation(BaseModel):
    """A YNAB payee location (GPS data from mobile apps).

    Attributes:
        id: Payee location UUID.
        payee_id: Parent payee UUID.
        latitude: GPS latitude, or None if not set.
        longitude: GPS longitude, or None if not set.
        deleted: Whether payee location is deleted.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    payee_id: str
    latitude: float | None = None
    longitude: float | None = None
    deleted: bool


class UserResponse(BaseModel):
    """Response for the GET /user endpoint.

    Attributes:
        id: User UUID.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
