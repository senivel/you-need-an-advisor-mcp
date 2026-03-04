"""Tests for Account, Category, CategoryGroup, Transaction models."""

from ynab_mcp.models import (
    Account,
    Category,
    CategoryGroup,
    CategoryGroupWithCategories,
    SubTransaction,
    TransactionDetail,
)


class TestAccountModel:
    """Tests for the Account Pydantic model."""

    def test_validates_required_fields(self):
        data = {
            "id": "acct-001",
            "name": "Checking",
            "type": "checking",
            "on_budget": True,
            "closed": False,
            "balance": 1234.56,
            "cleared_balance": 1200.00,
            "uncleared_balance": 34.56,
            "deleted": False,
        }
        account = Account.model_validate(data)
        assert account.id == "acct-001"
        assert account.name == "Checking"
        assert account.type == "checking"
        assert account.on_budget is True
        assert account.closed is False
        assert account.balance == 1234.56
        assert account.cleared_balance == 1200.00
        assert account.uncleared_balance == 34.56
        assert account.deleted is False

    def test_optional_fields_default_to_none(self):
        data = {
            "id": "acct-001",
            "name": "Checking",
            "type": "checking",
            "on_budget": True,
            "closed": False,
            "balance": 0.0,
            "cleared_balance": 0.0,
            "uncleared_balance": 0.0,
            "deleted": False,
        }
        account = Account.model_validate(data)
        assert account.note is None
        assert account.transfer_payee_id is None

    def test_ignores_extra_fields(self):
        data = {
            "id": "acct-001",
            "name": "Checking",
            "type": "checking",
            "on_budget": True,
            "closed": False,
            "balance": 0.0,
            "cleared_balance": 0.0,
            "uncleared_balance": 0.0,
            "deleted": False,
            "direct_import_linked": True,
            "last_reconciled_at": "2026-01-01",
        }
        account = Account.model_validate(data)
        assert account.name == "Checking"


class TestCategoryModel:
    """Tests for the Category Pydantic model."""

    def test_validates_required_fields(self):
        data = {
            "id": "cat-001",
            "category_group_id": "grp-001",
            "name": "Groceries",
            "hidden": False,
            "budgeted": 500.00,
            "activity": -123.45,
            "balance": 376.55,
            "deleted": False,
        }
        category = Category.model_validate(data)
        assert category.id == "cat-001"
        assert category.category_group_id == "grp-001"
        assert category.name == "Groceries"
        assert category.hidden is False
        assert category.budgeted == 500.00
        assert category.activity == -123.45
        assert category.balance == 376.55
        assert category.deleted is False

    def test_optional_goal_fields(self):
        data = {
            "id": "cat-001",
            "category_group_id": "grp-001",
            "name": "Groceries",
            "hidden": False,
            "budgeted": 500.00,
            "activity": -123.45,
            "balance": 376.55,
            "deleted": False,
            "goal_type": "NEED",
            "goal_target": 600.0,
            "goal_target_month": "2026-04-01",
            "goal_percentage_complete": 83,
            "goal_months_to_budget": 1,
            "goal_under_funded": 100.0,
            "goal_overall_funded": 500.0,
            "goal_overall_left": 100.0,
        }
        category = Category.model_validate(data)
        assert category.goal_type == "NEED"
        assert category.goal_target == 600.0
        assert category.goal_percentage_complete == 83

    def test_optional_fields_default_to_none(self):
        data = {
            "id": "cat-001",
            "category_group_id": "grp-001",
            "name": "Groceries",
            "hidden": False,
            "budgeted": 0.0,
            "activity": 0.0,
            "balance": 0.0,
            "deleted": False,
        }
        category = Category.model_validate(data)
        assert category.note is None
        assert category.goal_type is None
        assert category.goal_target is None
        assert category.category_group_name is None

    def test_ignores_extra_fields(self):
        data = {
            "id": "cat-001",
            "category_group_id": "grp-001",
            "name": "Groceries",
            "hidden": False,
            "budgeted": 0.0,
            "activity": 0.0,
            "balance": 0.0,
            "deleted": False,
            "original_category_group_id": "grp-999",
            "goal_snoozed_at": "2026-01-01",
        }
        category = Category.model_validate(data)
        assert category.name == "Groceries"


class TestCategoryGroupModel:
    """Tests for the CategoryGroup Pydantic model."""

    def test_validates_required_fields(self):
        data = {
            "id": "grp-001",
            "name": "Bills",
            "hidden": False,
            "deleted": False,
        }
        group = CategoryGroup.model_validate(data)
        assert group.id == "grp-001"
        assert group.name == "Bills"
        assert group.hidden is False
        assert group.deleted is False

    def test_ignores_extra_fields(self):
        data = {
            "id": "grp-001",
            "name": "Bills",
            "hidden": False,
            "deleted": False,
            "some_future_field": "value",
        }
        group = CategoryGroup.model_validate(data)
        assert group.name == "Bills"


class TestCategoryGroupWithCategoriesModel:
    """Tests for the CategoryGroupWithCategories Pydantic model."""

    def test_includes_categories_list(self):
        data = {
            "id": "grp-001",
            "name": "Bills",
            "hidden": False,
            "deleted": False,
            "categories": [
                {
                    "id": "cat-001",
                    "category_group_id": "grp-001",
                    "name": "Rent",
                    "hidden": False,
                    "budgeted": 1500.00,
                    "activity": -1500.00,
                    "balance": 0.0,
                    "deleted": False,
                },
            ],
        }
        group = CategoryGroupWithCategories.model_validate(data)
        assert group.name == "Bills"
        assert len(group.categories) == 1
        assert group.categories[0].name == "Rent"

    def test_empty_categories_list(self):
        data = {
            "id": "grp-001",
            "name": "Empty Group",
            "hidden": False,
            "deleted": False,
            "categories": [],
        }
        group = CategoryGroupWithCategories.model_validate(data)
        assert group.categories == []


class TestSubTransactionModel:
    """Tests for the SubTransaction Pydantic model."""

    def test_validates_required_fields(self):
        """SubTransaction validates with all required fields."""
        data = {
            "id": "st-001",
            "transaction_id": "txn-001",
            "amount": -25.50,
            "deleted": False,
        }
        sub = SubTransaction.model_validate(data)
        assert sub.id == "st-001"
        assert sub.transaction_id == "txn-001"
        assert sub.amount == -25.50
        assert sub.deleted is False

    def test_optional_fields_default_to_none(self):
        """SubTransaction optional fields default to None."""
        data = {
            "id": "st-001",
            "transaction_id": "txn-001",
            "amount": -10.0,
            "deleted": False,
        }
        sub = SubTransaction.model_validate(data)
        assert sub.payee_id is None
        assert sub.payee_name is None
        assert sub.category_id is None
        assert sub.category_name is None
        assert sub.memo is None
        assert sub.transfer_account_id is None
        assert sub.transfer_transaction_id is None

    def test_accepts_optional_fields(self):
        """SubTransaction accepts all optional fields."""
        data = {
            "id": "st-001",
            "transaction_id": "txn-001",
            "amount": -25.50,
            "deleted": False,
            "payee_id": "pay-001",
            "payee_name": "Grocery Store",
            "category_id": "cat-001",
            "category_name": "Groceries",
            "memo": "Split purchase",
            "transfer_account_id": "acct-002",
            "transfer_transaction_id": "txn-002",
        }
        sub = SubTransaction.model_validate(data)
        assert sub.payee_name == "Grocery Store"
        assert sub.category_name == "Groceries"
        assert sub.memo == "Split purchase"

    def test_ignores_extra_fields(self):
        """SubTransaction ignores unknown fields."""
        data = {
            "id": "st-001",
            "transaction_id": "txn-001",
            "amount": -10.0,
            "deleted": False,
            "future_field": "unknown",
        }
        sub = SubTransaction.model_validate(data)
        assert sub.id == "st-001"


class TestTransactionDetailModel:
    """Tests for the TransactionDetail Pydantic model."""

    def _minimal_txn(self, **overrides):
        """Build a minimal valid TransactionDetail dict.

        Returns:
            A dict with all required TransactionDetail fields.
        """
        base = {
            "id": "txn-001",
            "date": "2026-03-01",
            "amount": -45.67,
            "account_id": "acct-001",
            "account_name": "Checking",
            "approved": True,
            "cleared": "cleared",
            "deleted": False,
        }
        base.update(overrides)
        return base

    def test_validates_required_fields(self):
        """TransactionDetail validates a full API response with required fields."""
        txn = TransactionDetail.model_validate(self._minimal_txn())
        assert txn.id == "txn-001"
        assert txn.date == "2026-03-01"
        assert txn.amount == -45.67
        assert txn.account_id == "acct-001"
        assert txn.account_name == "Checking"
        assert txn.approved is True
        assert txn.cleared == "cleared"
        assert txn.deleted is False

    def test_optional_fields_default_to_none(self):
        """TransactionDetail optional fields default to None."""
        txn = TransactionDetail.model_validate(self._minimal_txn())
        assert txn.memo is None
        assert txn.payee_id is None
        assert txn.payee_name is None
        assert txn.category_id is None
        assert txn.category_name is None
        assert txn.transfer_account_id is None
        assert txn.transfer_transaction_id is None
        assert txn.matched_transaction_id is None
        assert txn.import_id is None
        assert txn.import_payee_name is None
        assert txn.import_payee_name_original is None
        assert txn.flag_color is None
        assert txn.flag_name is None
        assert txn.debt_transaction_type is None

    def test_accepts_optional_fields(self):
        """TransactionDetail accepts optional/nullable fields."""
        data = self._minimal_txn(
            memo="Coffee run",
            payee_id="pay-001",
            payee_name="Starbucks",
            category_id="cat-001",
            category_name="Dining Out",
            flag_color="red",
            flag_name="Important",
            import_id="YNAB:12345",
            import_payee_name="STARBUCKS #123",
            import_payee_name_original="STARBUCKS #123 ORIG",
            transfer_account_id="acct-002",
            transfer_transaction_id="txn-002",
            matched_transaction_id="txn-003",
            debt_transaction_type="payment",
        )
        txn = TransactionDetail.model_validate(data)
        assert txn.memo == "Coffee run"
        assert txn.payee_name == "Starbucks"
        assert txn.flag_color == "red"
        assert txn.debt_transaction_type == "payment"

    def test_ignores_extra_fields(self):
        """TransactionDetail ignores unknown fields (extra='ignore')."""
        data = self._minimal_txn(
            some_future_field="value",
            another_unknown=42,
        )
        txn = TransactionDetail.model_validate(data)
        assert txn.id == "txn-001"

    def test_subtransactions_defaults_to_empty_list(self):
        """TransactionDetail.subtransactions defaults to empty list."""
        txn = TransactionDetail.model_validate(self._minimal_txn())
        assert txn.subtransactions == []

    def test_subtransactions_parses_list(self):
        """TransactionDetail.subtransactions is a list of SubTransaction."""
        data = self._minimal_txn(
            subtransactions=[
                {
                    "id": "st-001",
                    "transaction_id": "txn-001",
                    "amount": -20.0,
                    "deleted": False,
                    "category_id": "cat-001",
                    "category_name": "Groceries",
                },
                {
                    "id": "st-002",
                    "transaction_id": "txn-001",
                    "amount": -25.67,
                    "deleted": False,
                    "category_id": "cat-002",
                    "category_name": "Household",
                },
            ],
        )
        txn = TransactionDetail.model_validate(data)
        assert len(txn.subtransactions) == 2
        assert isinstance(txn.subtransactions[0], SubTransaction)
        assert txn.subtransactions[0].amount == -20.0
        assert txn.subtransactions[1].category_name == "Household"
