# Payee Tools

Payees are the people and businesses you exchange money with -- your landlord, the grocery store, your employer. Payee tools let you browse your payee list, view details, rename payees for consistency, and check payee locations. Clean payee names make your transaction history easier to read and your reports more meaningful.

YNAB automatically creates payees from imported transactions, which can lead to inconsistencies (like "AMAZON.COM" and "Amazon" as separate payees). Renaming helps you keep things tidy.

## Usage Examples

> **You:** Show me my payees.
>
> **Claude** calls `manage_payees` with action `list` and responds:
>
> _47 payees found:_
> _- Amazon_
> _- Chipotle_
> _- Electric Company_
> _- Employer Inc_
> _- Whole Foods_
> _..._

> **You:** I want to see transfer payees too.
>
> **Claude** calls `manage_payees` with action `list` and `include_transfers=true`:
>
> _52 payees found (including transfers):_
> _- Amazon_
> _- Transfer : Checking_
> _- Transfer : Savings_
> _..._

> **You:** Rename "AMZN MKTP" to "Amazon".
>
> **Claude** calls `manage_payees` with action `update_name`:
>
> _Payee renamed: "AMZN MKTP" is now "Amazon"_

> **You:** Does Whole Foods have a location on file?
>
> **Claude** calls `manage_payees` with action `get_location` and responds:
>
> _Whole Foods -- Location:_
> _Latitude: 40.7128, Longitude: -74.0060_

## Available Actions

| Action           | Description                                    |
| ---------------- | ---------------------------------------------- |
| `list`           | List all payees (optionally include transfers) |
| `get`            | Get details for a specific payee               |
| `update_name`    | Rename a payee                                 |
| `list_locations` | List all payee locations                       |
| `get_location`   | Get location details for a specific payee      |

---

## API Reference

<!-- prettier-ignore -->
::: ynab_mcp.tools.payees.manage_payees
    options:
      show_root_heading: true
      show_source: true
