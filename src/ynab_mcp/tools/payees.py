"""Payee tools: list, detail, rename, and payee location tools."""

from fastmcp import Context

from ynab_mcp.app import AppContext, mcp
from ynab_mcp.budget_resolver import resolve_budget


@mcp.tool
async def list_payees(
    ctx: Context,
    budget_id_or_name: str = "last-used",
    include_transfers: bool = False,  # noqa: FBT001, FBT002
) -> str:
    """List all payees in a YNAB budget.

    Returns a count header followed by each payee's name and ID. Deleted
    payees are always excluded. Transfer payees (linked to account transfers)
    are excluded by default unless ``include_transfers`` is True.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        include_transfers: If True, include transfer payees. Defaults to False.

    Returns:
        Structured text with count header and payee lines,
        or "No payees found." if none match.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    data = await app.client.get(f"/budgets/{budget_id}/payees")
    all_payees = data["payees"]

    # Exclude deleted
    payees = [p for p in all_payees if not p["deleted"]]

    # Exclude transfers unless requested
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


@mcp.tool
async def get_payee(
    ctx: Context,
    payee_id: str,
    budget_id_or_name: str = "last-used",
) -> str:
    """Get detailed information about a specific YNAB payee.

    Returns the payee name, ID, and transfer account info if applicable.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        payee_id: The payee UUID.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Structured text with payee details.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    data = await app.client.get(f"/budgets/{budget_id}/payees/{payee_id}")
    payee = data["payee"]

    lines = [
        f"Payee: {payee['name']}",
        f"  ID: {payee['id']}",
    ]
    if payee.get("transfer_account_id"):
        lines.append(f"  Transfer account: {payee['transfer_account_id']}")

    return "\n".join(lines)


@mcp.tool
async def update_payee_name(
    ctx: Context,
    payee_id: str,
    name: str,
    budget_id_or_name: str = "last-used",
) -> str:
    """Rename a YNAB payee.

    Sends a PATCH request to update the payee's name and returns
    a confirmation with the new name and payee ID.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        payee_id: The payee UUID to rename.
        name: The new name for the payee.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Confirmation text with the updated payee name and ID.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    data = await app.client.patch(
        f"/budgets/{budget_id}/payees/{payee_id}",
        json={"payee": {"name": name}},
    )
    payee = data["payee"]

    return f"Payee renamed to '{payee['name']}'.\n  ID: {payee['id']}"


@mcp.tool
async def list_payee_locations(
    ctx: Context,
    budget_id_or_name: str = "last-used",
    payee_id: str | None = None,
) -> str:
    """List payee locations in a YNAB budget.

    Without ``payee_id``: returns all payee locations across all payees.
    With ``payee_id``: returns locations for a specific payee only.
    Deleted locations are always excluded.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".
        payee_id: If provided, filter locations to this payee only.

    Returns:
        Structured text with count header and location lines,
        or "No payee locations found." if none exist.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

    if payee_id:
        path = f"/budgets/{budget_id}/payees/{payee_id}/payee_locations"
    else:
        path = f"/budgets/{budget_id}/payee_locations"

    data = await app.client.get(path)
    all_locations = data["payee_locations"]

    # Exclude deleted
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


@mcp.tool
async def get_payee_location(
    ctx: Context,
    payee_location_id: str,
    budget_id_or_name: str = "last-used",
) -> str:
    """Get detailed information about a specific payee location.

    Returns the location ID, payee ID, latitude, and longitude.

    Args:
        ctx: The MCP context providing access to lifespan dependencies.
        payee_location_id: The payee location UUID.
        budget_id_or_name: Budget UUID or name. Defaults to "last-used".

    Returns:
        Structured text with payee location details.
    """
    app: AppContext = ctx.lifespan_context
    budget_id, _info = await resolve_budget(
        app.client, budget_id_or_name, cache=app.cache
    )

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
