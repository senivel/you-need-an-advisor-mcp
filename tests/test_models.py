"""Tests for Account, Category, CategoryGroup models."""

from ynab_mcp.models import (
    Account,
    Category,
    CategoryGroup,
    CategoryGroupWithCategories,
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
