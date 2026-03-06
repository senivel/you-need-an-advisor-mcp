"""In-memory delta cache for YNAB API responses.

Tracks ``server_knowledge`` per endpoint and merges delta responses
into cached data. Provides cache key extraction from API paths and
mutation-based invalidation with cross-resource rules.

All 8 resource-level delta-capable YNAB endpoints are supported.
The cache is fully transparent to tools -- only ``YNABClient`` interacts
with it directly.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger(__name__)

DELTA_ENDPOINTS: frozenset[str] = frozenset({
    "accounts",
    "categories",
    "months",
    "payees",
    "transactions",
    "scheduled_transactions",
    "money_movements",
    "money_movement_groups",
})
"""Resource-level endpoints that support delta requests via ``server_knowledge``."""

CROSS_INVALIDATION_MAP: dict[str, list[str]] = {
    "transactions": ["accounts", "categories"],
    "categories": ["months"],
}
"""Resources to additionally invalidate when a given resource is mutated."""

_BUDGET_RESOURCE_PATTERN: re.Pattern[str] = re.compile(
    r"^/budgets/([^/]+)/(" + "|".join(DELTA_ENDPOINTS) + r")$",
)


@dataclass
class CacheEntry:
    """A single cached API response with its server_knowledge value.

    Attributes:
        server_knowledge: The YNAB server knowledge integer for this entry.
        data: The full response data dict (with milliunit conversion applied).
    """

    server_knowledge: int
    data: dict[str, Any]


@dataclass
class TTLCacheEntry:
    """A cached value with a time-to-live expiration.

    Attributes:
        data: The cached data dict.
        expires_at: Monotonic clock timestamp when this entry expires.
    """

    data: dict[str, Any]
    expires_at: float


class CacheStore:
    """In-memory cache for YNAB delta-capable endpoints.

    Stores full response data and ``server_knowledge`` values per
    budget+endpoint combination. Merges delta responses by
    replacing/adding changed entities in the cached list.

    Attributes:
        _entries: Internal dict mapping cache keys to CacheEntry instances.
    """

    def __init__(self) -> None:
        """Initialize an empty cache store."""
        self._entries: dict[str, CacheEntry] = {}
        self._ttl_entries: dict[str, TTLCacheEntry] = {}

    def get_knowledge(self, cache_key: str) -> int | None:
        """Return stored server_knowledge for a cache key, or None.

        Args:
            cache_key: The cache key in ``{budget_id}:{resource}`` format.

        Returns:
            The server_knowledge integer, or None if not cached.
        """
        entry = self._entries.get(cache_key)
        return entry.server_knowledge if entry else None

    def get_cached_data(self, cache_key: str) -> dict[str, Any] | None:
        """Return cached response data, or None if not cached.

        Args:
            cache_key: The cache key in ``{budget_id}:{resource}`` format.

        Returns:
            The cached data dict, or None if not cached.
        """
        entry = self._entries.get(cache_key)
        return entry.data if entry else None

    def update(
        self,
        cache_key: str,
        server_knowledge: int,
        data: dict[str, Any],
    ) -> None:
        """Store or replace a cache entry with full response data.

        Args:
            cache_key: The cache key in ``{budget_id}:{resource}`` format.
            server_knowledge: The YNAB server knowledge value.
            data: The full response data dict.
        """
        self._entries[cache_key] = CacheEntry(
            server_knowledge=server_knowledge,
            data=data,
        )

    def merge_delta(
        self,
        cache_key: str,
        server_knowledge: int,
        delta_data: dict[str, Any],
    ) -> None:
        """Merge delta entities into existing cached data.

        For each top-level key in ``delta_data`` that is a list of dicts
        with ``id`` fields: updates existing entities, adds new ones, and
        removes those with ``deleted=True``.

        For ``category_groups`` (grouped response): merges at group level
        first, then merges categories within each group.

        If no existing entry exists, stores ``delta_data`` as a fresh entry.

        Args:
            cache_key: The cache key in ``{budget_id}:{resource}`` format.
            server_knowledge: The new server knowledge value.
            delta_data: The delta response data dict.
        """
        existing = self.get_cached_data(cache_key)
        if existing is None:
            self.update(cache_key, server_knowledge, delta_data)
            return

        for key, value in delta_data.items():
            if not isinstance(value, list):
                existing[key] = value
                continue

            if key == "category_groups":
                self._merge_category_groups(existing, value)
            else:
                existing[key] = self._merge_entity_list(
                    existing.get(key, []),
                    value,
                )

        self._entries[cache_key] = CacheEntry(
            server_knowledge=server_knowledge,
            data=existing,
        )

    def invalidate(self, cache_key: str) -> None:
        """Remove a specific cache entry.

        Args:
            cache_key: The cache key to remove.
        """
        self._entries.pop(cache_key, None)

    def invalidate_budget(self, budget_id: str) -> None:
        """Remove all cache entries for a budget.

        Args:
            budget_id: The YNAB budget ID whose entries to remove.
        """
        keys_to_remove = [k for k in self._entries if k.startswith(f"{budget_id}:")]
        for key in keys_to_remove:
            del self._entries[key]

    def invalidate_for_mutation(self, path: str) -> None:
        """Invalidate cache entries affected by a mutation at the given path.

        Extracts the budget ID and resource type from the API path,
        invalidates the direct resource, then invalidates any cross-resource
        entries defined in :data:`CROSS_INVALIDATION_MAP`.

        Args:
            path: The API path of the mutation (e.g., ``/budgets/b1/transactions/t1``).
        """
        parts = path.strip("/").split("/")
        if len(parts) < 3 or parts[0] != "budgets":  # noqa: PLR2004
            return

        budget_id = parts[1]
        resource = parts[2]

        self.invalidate(f"{budget_id}:{resource}")

        for cross_resource in CROSS_INVALIDATION_MAP.get(resource, []):
            self.invalidate(f"{budget_id}:{cross_resource}")

    def get_ttl(self, key: str) -> dict[str, Any] | None:
        """Return cached data for a TTL key, or None if missing/expired.

        Expired entries are deleted on access.

        Args:
            key: The TTL cache key.

        Returns:
            The cached data dict, or None if not cached or expired.
        """
        entry = self._ttl_entries.get(key)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._ttl_entries[key]
            return None
        return entry.data

    def set_ttl(
        self,
        key: str,
        data: dict[str, Any],
        ttl_seconds: float,
    ) -> None:
        """Store data with a time-to-live expiration.

        Args:
            key: The TTL cache key.
            data: The data dict to cache.
            ttl_seconds: Number of seconds until the entry expires.
        """
        self._ttl_entries[key] = TTLCacheEntry(
            data=data,
            expires_at=time.monotonic() + ttl_seconds,
        )

    def clear(self) -> None:
        """Remove all cache entries (both delta and TTL)."""
        self._entries.clear()
        self._ttl_entries.clear()

    @staticmethod
    def _merge_entity_list(
        existing: list[dict[str, Any]],
        delta: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge delta entities into an existing entity list by ``id`` field.

        Updates existing entities, adds new ones, removes deleted ones.

        Args:
            existing: The current cached list of entities.
            delta: The delta list of changed entities.

        Returns:
            The merged entity list.
        """
        by_id: dict[str, dict[str, Any]] = {e["id"]: e for e in existing}

        for entity in delta:
            entity_id = entity["id"]
            if entity.get("deleted"):
                by_id.pop(entity_id, None)
            else:
                by_id[entity_id] = entity

        return list(by_id.values())

    @staticmethod
    def _merge_category_groups(
        existing: dict[str, Any],
        delta_groups: list[dict[str, Any]],
    ) -> None:
        """Merge delta category groups into existing cached data.

        Merges at group level first, then merges categories within
        each group by their ``id`` field.

        Args:
            existing: The existing cached data dict (modified in-place).
            delta_groups: The delta list of category groups.
        """
        groups_by_id: dict[str, dict[str, Any]] = {
            g["id"]: g for g in existing.get("category_groups", [])
        }

        for delta_group in delta_groups:
            group_id = delta_group["id"]
            if delta_group.get("deleted"):
                groups_by_id.pop(group_id, None)
                continue

            existing_group = groups_by_id.get(group_id)
            if existing_group is None:
                groups_by_id[group_id] = delta_group
                continue

            # Merge categories within the group
            delta_cats = delta_group.get("categories", [])
            existing_cats = existing_group.get("categories", [])
            merged_cats = CacheStore._merge_entity_list(existing_cats, delta_cats)
            existing_group["categories"] = merged_cats

            # Update other group-level fields
            for key, value in delta_group.items():
                if key != "categories":
                    existing_group[key] = value

        existing["category_groups"] = list(groups_by_id.values())


def cache_key_from_path(path: str) -> str | None:
    """Extract a cache key from an API path, or None if not delta-cacheable.

    Matches paths like ``/budgets/{budget_id}/{resource}`` where resource
    is in :data:`DELTA_ENDPOINTS`.

    Args:
        path: The API path (e.g., ``/budgets/abc-123/transactions``).

    Returns:
        A cache key like ``abc-123:transactions``, or None if the path
        is not a delta-capable endpoint.
    """
    match = _BUDGET_RESOURCE_PATTERN.match(path)
    if match:
        budget_id, resource = match.groups()
        return f"{budget_id}:{resource}"
    return None


def strip_server_knowledge(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of data with the ``server_knowledge`` key removed.

    Args:
        data: The response data dict that may contain ``server_knowledge``.

    Returns:
        A shallow copy of ``data`` without the ``server_knowledge`` key.
    """
    return {k: v for k, v in data.items() if k != "server_knowledge"}
