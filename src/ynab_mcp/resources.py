"""MCP Resource definitions for YNAB budget structure.

Exposes budget accounts, categories, and payees as MCP Resources
at ``ynab://`` URIs. LLMs can read these resources upfront to
understand budget structure without repeated tool calls.

All resources return JSON strings with filtered, current data.
Deleted entities are always excluded. Categories also exclude
hidden items, and payees exclude transfer payees.
"""

import json
from typing import Any

from fastmcp import Context

from ynab_mcp.server import mcp


@mcp.resource("ynab://budgets/{budget_id}/accounts")
async def budget_accounts(budget_id: str, ctx: Context) -> str:
    """List all active accounts in a budget with current balances.

    Returns a JSON array of non-deleted accounts, each containing
    id, name, type, on_budget, closed, and balance fields.

    Args:
        budget_id: The YNAB budget ID.
        ctx: The MCP context with lifespan dependencies.

    Returns:
        JSON string of account objects.
    """
    app = ctx.lifespan_context
    data: dict[str, Any] = await app.client.get(
        f"/budgets/{budget_id}/accounts",
    )

    accounts = [
        {
            "id": acct["id"],
            "name": acct["name"],
            "type": acct["type"],
            "on_budget": acct["on_budget"],
            "closed": acct["closed"],
            "balance": acct["balance"],
        }
        for acct in data["accounts"]
        if not acct["deleted"]
    ]

    return json.dumps(accounts, indent=2)


@mcp.resource("ynab://budgets/{budget_id}/categories")
async def budget_categories(budget_id: str, ctx: Context) -> str:
    """List all active category groups and categories with budget amounts.

    Returns a JSON array of non-deleted category groups, each containing
    a group name and nested array of non-deleted, non-hidden categories
    with id, name, budgeted, activity, and balance fields.

    Groups with no visible categories after filtering are excluded.

    Args:
        budget_id: The YNAB budget ID.
        ctx: The MCP context with lifespan dependencies.

    Returns:
        JSON string of category group objects.
    """
    app = ctx.lifespan_context
    data: dict[str, Any] = await app.client.get(
        f"/budgets/{budget_id}/categories",
    )

    groups = []
    for group in data["category_groups"]:
        if group["deleted"]:
            continue

        visible_cats = [
            {
                "id": cat["id"],
                "name": cat["name"],
                "budgeted": cat["budgeted"],
                "activity": cat["activity"],
                "balance": cat["balance"],
            }
            for cat in group["categories"]
            if not cat["deleted"] and not cat["hidden"]
        ]

        if visible_cats:
            groups.append({
                "group": group["name"],
                "categories": visible_cats,
            })

    return json.dumps(groups, indent=2)


@mcp.resource("ynab://budgets/{budget_id}/payees")
async def budget_payees(budget_id: str, ctx: Context) -> str:
    """List all non-transfer payees in a budget.

    Returns a JSON array of non-deleted, non-transfer payees with
    id and name fields. Transfer payees (those linked to an account)
    are excluded.

    Args:
        budget_id: The YNAB budget ID.
        ctx: The MCP context with lifespan dependencies.

    Returns:
        JSON string of payee objects.
    """
    app = ctx.lifespan_context
    data: dict[str, Any] = await app.client.get(
        f"/budgets/{budget_id}/payees",
    )

    payees = [
        {
            "id": payee["id"],
            "name": payee["name"],
        }
        for payee in data["payees"]
        if not payee["deleted"] and payee.get("transfer_account_id") is None
    ]

    return json.dumps(payees, indent=2)
