"""Payee tools: list, detail, rename, and payee location tools."""

from typing import Literal, cast

from fastmcp import Context
from fastmcp.exceptions import ToolError

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget


async def _list_payees(
    app: AppContext,
    budget_id: str,
    *,
    include_transfers: bool = False,
) -> str:
    """List all payees in a budget.

    Returns:
        Structured text with count header and payee lines.
    """
    data = await app.client.get(f"/budgets/{budget_id}/payees")
    all_payees = data["payees"]
    payees = [p for p in all_payees if not p["deleted"]]
    if not include_transfers:
        payees = [p for p in payees if p.get("transfer_account_id") is None]
    if not payees:
        return "No payees found."
    count = len(payees)
    noun = "payee" if count == 1 else "payees"
    lines = [f"{count} {noun} found:"]
    for p in payees:
        lines.extend((f"- {p['name']}", f"  ID: {p['id']}"))
    return "\n".join(lines)


async def _get_payee(
    app: AppContext,
    budget_id: str,
    *,
    payee_id: str,
) -> str:
    """Get detailed information about a specific payee.

    Returns:
        Structured text with payee details.
    """
    data = await app.client.get(f"/budgets/{budget_id}/payees/{payee_id}")
    payee = data["payee"]
    lines = [
        f"Payee: {payee['name']}",
        f"  ID: {payee['id']}",
    ]
    if payee.get("transfer_account_id"):
        lines.append(f"  Transfer account: {payee['transfer_account_id']}")
    return "\n".join(lines)


async def _update_name(
    app: AppContext,
    budget_id: str,
    *,
    payee_id: str,
    name: str,
) -> str:
    """Rename a payee.

    Returns:
        Confirmation text with the updated payee name and ID.
    """
    data = await app.client.patch(
        f"/budgets/{budget_id}/payees/{payee_id}",
        json={"payee": {"name": name}},
    )
    payee = data["payee"]
    return f"Payee renamed to '{payee['name']}'.\n  ID: {payee['id']}"


async def _list_locations(
    app: AppContext,
    budget_id: str,
    *,
    payee_id: str | None = None,
) -> str:
    """List payee locations, optionally filtered by payee.

    Returns:
        Structured text with count header and location lines.
    """
    if payee_id:
        path = f"/budgets/{budget_id}/payees/{payee_id}/payee_locations"
    else:
        path = f"/budgets/{budget_id}/payee_locations"
    data = await app.client.get(path)
    all_locations = data["payee_locations"]
    locations = [loc for loc in all_locations if not loc["deleted"]]
    if not locations:
        return "No payee locations found."
    count = len(locations)
    noun = "payee location" if count == 1 else "payee locations"
    lines = [f"{count} {noun} found:"]
    for loc in locations:
        lines.extend((
            f"- {loc['payee_id']} | lat: {loc['latitude']}, lon: {loc['longitude']}",
            f"  ID: {loc['id']}",
        ))
    return "\n".join(lines)


async def _get_location(
    app: AppContext,
    budget_id: str,
    *,
    payee_location_id: str,
) -> str:
    """Get detailed information about a specific payee location.

    Returns:
        Structured text with payee location details.
    """
    data = await app.client.get(
        f"/budgets/{budget_id}/payee_locations/{payee_location_id}",
    )
    loc = data["payee_location"]
    return (
        f"Payee location:\n"
        f"  ID: {loc['id']}\n"
        f"  Payee ID: {loc['payee_id']}\n"
        f"  Latitude: {loc['latitude']}\n"
        f"  Longitude: {loc['longitude']}"
    )


@mcp.tool
async def manage_payees(  # noqa: PLR0913, PLR0917
    ctx: Context,
    action: Literal["list", "get", "update_name", "list_locations", "get_location"],
    budget_id_or_name: str = "last-used",
    include_transfers: bool = False,  # noqa: FBT001, FBT002
    payee_id: str | None = None,
    name: str | None = None,
    payee_location_id: str | None = None,
) -> str:
    """Manage YNAB payees: list, get details, rename, and query locations.

    Actions:
        list: List all payees. Uses budget_id_or_name, include_transfers.
        get: Get payee details. Uses payee_id (required).
        update_name: Rename payee. Uses payee_id (required), name (required).
        list_locations: List payee locations. Uses payee_id (optional filter).
        get_location: Get location details. Uses payee_location_id (required).

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        action: The operation to perform.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        include_transfers: If True, include transfer payees (list only).
        payee_id: The payee UUID (get, update_name, list_locations).
        name: New name for the payee (update_name only).
        payee_location_id: The payee location UUID (get_location only).

    Returns:
        Structured text with payee information or confirmation.

    Raises:
        ToolError: If required parameters for the action are missing.
    """
    app = cast("AppContext", ctx.lifespan_context)
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    if action == "list":
        return await _list_payees(app, budget_id, include_transfers=include_transfers)
    if action == "get":
        if payee_id is None:
            msg = "payee_id is required for action='get'"
            raise ToolError(msg)
        return await _get_payee(app, budget_id, payee_id=payee_id)
    if action == "update_name":
        if payee_id is None or name is None:
            msg = "payee_id and name are required for action='update_name'"
            raise ToolError(msg)
        return await _update_name(app, budget_id, payee_id=payee_id, name=name)
    if action == "list_locations":
        return await _list_locations(app, budget_id, payee_id=payee_id)
    if payee_location_id is None:
        msg = "payee_location_id is required for action='get_location'"
        raise ToolError(msg)
    return await _get_location(app, budget_id, payee_location_id=payee_location_id)
