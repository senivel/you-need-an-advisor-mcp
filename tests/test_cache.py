"""Tests for CacheStore with delta merging and invalidation."""

import pytest

from ynab_mcp.cache import (
    CROSS_INVALIDATION_MAP,
    DELTA_ENDPOINTS,
    CacheStore,
    cache_key_from_path,
    strip_server_knowledge,
)


class TestCacheStoreBasics:
    """Tests for basic get/update operations."""

    def test_get_knowledge_returns_none_for_unknown_key(self):
        """Fresh cache returns None for unknown keys."""
        store = CacheStore()
        assert store.get_knowledge("budget-1:accounts") is None

    def test_get_cached_data_returns_none_for_unknown_key(self):
        """Fresh cache returns None for unknown keys."""
        store = CacheStore()
        assert store.get_cached_data("budget-1:accounts") is None

    def test_update_stores_knowledge_and_data(self):
        """Update stores data and server_knowledge, both retrievable."""
        store = CacheStore()
        data = {"accounts": [{"id": "a1", "name": "Checking"}]}
        store.update("budget-1:accounts", 42, data)

        assert store.get_knowledge("budget-1:accounts") == 42
        assert store.get_cached_data("budget-1:accounts") == data


class TestDeltaMerging:
    """Tests for merge_delta with entity-level merging."""

    def test_merge_delta_adds_new_entities(self):
        """New entities in delta are added to cached data."""
        store = CacheStore()
        initial = {"accounts": [{"id": "a1", "name": "Checking"}]}
        store.update("b:accounts", 1, initial)

        delta = {"accounts": [{"id": "a2", "name": "Savings"}]}
        store.merge_delta("b:accounts", 2, delta)

        cached = store.get_cached_data("b:accounts")
        assert len(cached["accounts"]) == 2
        names = {a["name"] for a in cached["accounts"]}
        assert names == {"Checking", "Savings"}
        assert store.get_knowledge("b:accounts") == 2

    def test_merge_delta_updates_existing_entities(self):
        """Existing entities are updated by matching on id."""
        store = CacheStore()
        initial = {"accounts": [{"id": "a1", "name": "Old Name", "balance": 100}]}
        store.update("b:accounts", 1, initial)

        delta = {"accounts": [{"id": "a1", "name": "New Name", "balance": 200}]}
        store.merge_delta("b:accounts", 2, delta)

        cached = store.get_cached_data("b:accounts")
        assert len(cached["accounts"]) == 1
        assert cached["accounts"][0]["name"] == "New Name"
        assert cached["accounts"][0]["balance"] == 200

    def test_merge_delta_removes_deleted_entities(self):
        """Entities with deleted=True are removed from cache."""
        store = CacheStore()
        initial = {
            "accounts": [
                {"id": "a1", "name": "Keep"},
                {"id": "a2", "name": "Remove"},
            ]
        }
        store.update("b:accounts", 1, initial)

        delta = {"accounts": [{"id": "a2", "name": "Remove", "deleted": True}]}
        store.merge_delta("b:accounts", 2, delta)

        cached = store.get_cached_data("b:accounts")
        assert len(cached["accounts"]) == 1
        assert cached["accounts"][0]["id"] == "a1"

    def test_merge_delta_category_groups_nested(self):
        """Category groups merge at group level with nested categories."""
        store = CacheStore()
        initial = {
            "category_groups": [
                {
                    "id": "g1",
                    "name": "Bills",
                    "categories": [
                        {"id": "c1", "name": "Rent", "budgeted": 1000},
                        {"id": "c2", "name": "Electric", "budgeted": 100},
                    ],
                },
                {
                    "id": "g2",
                    "name": "Fun",
                    "categories": [
                        {"id": "c3", "name": "Dining", "budgeted": 200},
                    ],
                },
            ]
        }
        store.update("b:categories", 1, initial)

        delta = {
            "category_groups": [
                {
                    "id": "g1",
                    "name": "Bills",
                    "categories": [
                        {"id": "c2", "name": "Electric", "budgeted": 150},
                        {"id": "c4", "name": "Water", "budgeted": 50},
                    ],
                },
            ]
        }
        store.merge_delta("b:categories", 2, delta)

        cached = store.get_cached_data("b:categories")
        groups = cached["category_groups"]
        assert len(groups) == 2  # Both groups still exist

        bills = next(g for g in groups if g["id"] == "g1")
        cat_names = {c["name"] for c in bills["categories"]}
        assert cat_names == {"Rent", "Electric", "Water"}
        electric = next(c for c in bills["categories"] if c["id"] == "c2")
        assert electric["budgeted"] == 150

    def test_merge_delta_no_existing_data_stores_fresh(self):
        """merge_delta on unknown key stores data as new entry."""
        store = CacheStore()
        delta = {"accounts": [{"id": "a1", "name": "New"}]}
        store.merge_delta("b:accounts", 1, delta)

        cached = store.get_cached_data("b:accounts")
        assert cached == delta
        assert store.get_knowledge("b:accounts") == 1


class TestInvalidation:
    """Tests for invalidation methods."""

    def test_invalidate_removes_single_key(self):
        """Invalidate removes one specific cache entry."""
        store = CacheStore()
        store.update("b:accounts", 1, {"accounts": []})
        store.update("b:categories", 1, {"categories": []})

        store.invalidate("b:accounts")

        assert store.get_cached_data("b:accounts") is None
        assert store.get_cached_data("b:categories") is not None

    def test_invalidate_budget_removes_all_keys_for_budget(self):
        """invalidate_budget removes all entries for a budget_id."""
        store = CacheStore()
        store.update("budget-1:accounts", 1, {"accounts": []})
        store.update("budget-1:categories", 1, {"categories": []})
        store.update("budget-2:accounts", 1, {"accounts": []})

        store.invalidate_budget("budget-1")

        assert store.get_cached_data("budget-1:accounts") is None
        assert store.get_cached_data("budget-1:categories") is None
        assert store.get_cached_data("budget-2:accounts") is not None

    def test_invalidate_for_mutation_direct_resource(self):
        """invalidate_for_mutation clears the direct resource."""
        store = CacheStore()
        store.update("b1:accounts", 1, {"accounts": []})

        store.invalidate_for_mutation("/budgets/b1/accounts/a1")

        assert store.get_cached_data("b1:accounts") is None

    def test_invalidate_for_mutation_cross_resource_transactions(self):
        """Transaction mutations also invalidate accounts and categories."""
        store = CacheStore()
        store.update("b1:transactions", 1, {"transactions": []})
        store.update("b1:accounts", 1, {"accounts": []})
        store.update("b1:categories", 1, {"categories": []})
        store.update("b1:payees", 1, {"payees": []})

        store.invalidate_for_mutation("/budgets/b1/transactions/txn-1")

        assert store.get_cached_data("b1:transactions") is None
        assert store.get_cached_data("b1:accounts") is None
        assert store.get_cached_data("b1:categories") is None
        # Payees should NOT be invalidated
        assert store.get_cached_data("b1:payees") is not None

    def test_invalidate_for_mutation_cross_resource_categories(self):
        """Category mutations also invalidate months."""
        store = CacheStore()
        store.update("b1:categories", 1, {"categories": []})
        store.update("b1:months", 1, {"months": []})

        store.invalidate_for_mutation("/budgets/b1/categories/cat-1")

        assert store.get_cached_data("b1:categories") is None
        assert store.get_cached_data("b1:months") is None

    def test_clear_removes_all_entries(self):
        """Clear removes every cache entry."""
        store = CacheStore()
        store.update("b1:accounts", 1, {"accounts": []})
        store.update("b2:categories", 1, {"categories": []})

        store.clear()

        assert store.get_cached_data("b1:accounts") is None
        assert store.get_cached_data("b2:categories") is None


class TestCacheKeyFromPath:
    """Tests for cache_key_from_path function."""

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("/budgets/b1/accounts", "b1:accounts"),
            ("/budgets/b1/categories", "b1:categories"),
            ("/budgets/b1/months", "b1:months"),
            ("/budgets/b1/payees", "b1:payees"),
            ("/budgets/b1/transactions", "b1:transactions"),
            ("/budgets/b1/scheduled_transactions", "b1:scheduled_transactions"),
            ("/budgets/b1/money_movements", "b1:money_movements"),
            ("/budgets/b1/money_movement_groups", "b1:money_movement_groups"),
        ],
    )
    def test_delta_capable_paths(self, path, expected):
        """Delta-capable paths return correct cache keys."""
        assert cache_key_from_path(path) == expected

    @pytest.mark.parametrize(
        "path",
        [
            "/user",
            "/budgets",
            "/budgets/b1/accounts/a1",
            "/budgets/b1/months/2024-01-01",
            "/budgets/b1/categories/c1/transactions",
            "/budgets/b1/payees/p1/transactions",
        ],
    )
    def test_non_delta_paths_return_none(self, path):
        """Non-delta paths return None."""
        assert cache_key_from_path(path) is None


class TestDeltaEndpoints:
    """Tests for DELTA_ENDPOINTS frozenset."""

    def test_contains_all_expected_endpoints(self):
        """DELTA_ENDPOINTS contains exactly the 8 resource-level endpoints."""
        expected = {
            "accounts",
            "categories",
            "months",
            "payees",
            "transactions",
            "scheduled_transactions",
            "money_movements",
            "money_movement_groups",
        }
        assert expected == DELTA_ENDPOINTS

    def test_is_frozenset(self):
        """DELTA_ENDPOINTS is immutable."""
        assert isinstance(DELTA_ENDPOINTS, frozenset)


class TestCrossInvalidationMap:
    """Tests for CROSS_INVALIDATION_MAP."""

    def test_transactions_invalidate_accounts_and_categories(self):
        """Transaction mutations cross-invalidate accounts and categories."""
        assert "accounts" in CROSS_INVALIDATION_MAP["transactions"]
        assert "categories" in CROSS_INVALIDATION_MAP["transactions"]

    def test_categories_invalidate_months(self):
        """Category mutations cross-invalidate months."""
        assert "months" in CROSS_INVALIDATION_MAP["categories"]


class TestTTLCache:
    """Tests for TTL-based caching methods."""

    def test_get_ttl_returns_none_for_missing_key(self):
        """get_ttl returns None for a key that was never set."""
        store = CacheStore()
        assert store.get_ttl("budgets") is None

    def test_set_ttl_stores_data_and_get_ttl_retrieves_it(self, mocker):
        """set_ttl stores data, get_ttl retrieves it within TTL window."""
        mock_time = mocker.patch("ynab_mcp.cache.time")
        mock_time.monotonic.return_value = 1000.0

        store = CacheStore()
        store.set_ttl("budgets", {"budgets": [{"id": "b1"}]}, ttl_seconds=300.0)

        # Still within TTL window
        mock_time.monotonic.return_value = 1100.0
        result = store.get_ttl("budgets")
        assert result == {"budgets": [{"id": "b1"}]}

    def test_get_ttl_returns_none_after_ttl_expires(self, mocker):
        """get_ttl returns None and cleans up entry after TTL expires."""
        mock_time = mocker.patch("ynab_mcp.cache.time")
        mock_time.monotonic.return_value = 1000.0

        store = CacheStore()
        store.set_ttl("budgets", {"budgets": [{"id": "b1"}]}, ttl_seconds=300.0)

        # TTL expired
        mock_time.monotonic.return_value = 1301.0
        result = store.get_ttl("budgets")
        assert result is None

    def test_clear_removes_ttl_entries(self, mocker):
        """clear() removes TTL entries alongside delta entries."""
        mock_time = mocker.patch("ynab_mcp.cache.time")
        mock_time.monotonic.return_value = 1000.0

        store = CacheStore()
        store.update("b1:accounts", 1, {"accounts": []})
        store.set_ttl("budgets", {"budgets": [{"id": "b1"}]}, ttl_seconds=300.0)

        store.clear()

        assert store.get_cached_data("b1:accounts") is None
        mock_time.monotonic.return_value = 1001.0
        assert store.get_ttl("budgets") is None


class TestStripServerKnowledge:
    """Tests for strip_server_knowledge function."""

    def test_removes_server_knowledge_key(self):
        """server_knowledge is removed from returned data."""
        data = {"transactions": [{"id": "t1"}], "server_knowledge": 42}
        result = strip_server_knowledge(data)
        assert "server_knowledge" not in result
        assert result == {"transactions": [{"id": "t1"}]}

    def test_does_not_modify_original(self):
        """Original dict is not mutated."""
        data = {"transactions": [], "server_knowledge": 42}
        strip_server_knowledge(data)
        assert "server_knowledge" in data

    def test_returns_unchanged_if_no_server_knowledge(self):
        """Data without server_knowledge is returned as-is copy."""
        data = {"user": {"id": "abc"}}
        result = strip_server_knowledge(data)
        assert result == data
