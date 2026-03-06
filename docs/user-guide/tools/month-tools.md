# Month Tools

YNAB is built around monthly budgeting -- each month is a fresh start where you assign your available dollars to categories. Month tools give you the monthly view: income, budgeted amounts, spending activity, and the all-important "To Be Budgeted" number. You can also dig into money movement patterns to understand where your dollars are flowing.

The **Age of Money** metric is especially useful here -- it tells you how many days old the money you're spending today is. A higher age means you're spending older money, which is a sign of financial stability.

## Usage Examples

> **You:** How did last month go?
>
> **Claude** calls `manage_months` with action `get` for February 2026:
>
> _February 2026:_
> _Income: $5,400.00_
> _Budgeted: $5,200.00_
> _Activity: -$4,870.00_
> _To be budgeted: $200.00_
> _Age of money: 38 days_

> **You:** Show me all my budget months.
>
> **Claude** calls `manage_months` with action `list` and responds:
>
> _24 months found:_
> _- 2026-03-01 -- Income: $3,200.00 | Budgeted: $3,200.00 | TBB: $0.00_
> _- 2026-02-01 -- Income: $5,400.00 | Budgeted: $5,200.00 | TBB: $200.00_
> _- 2026-01-01 -- Income: $5,400.00 | Budgeted: $5,400.00 | TBB: $0.00_
> _..._

> **You:** Show me the money movements for this month.
>
> **Claude** calls `manage_months` with action `list_money_movements`:
>
> _Money movements for March 2026:_
> _- Groceries: -$423.17_
> _- Rent: -$1,500.00_
> _- Dining Out: -$142.30_
> _..._

> **You:** Break that down by category group.
>
> **Claude** calls `manage_months` with action `list_money_movement_groups`:
>
> _Money movements by group for March 2026:_
> _Monthly Bills: -$1,695.40_
> _Everyday Expenses: -$743.22_
> _Fun Money: -$178.29_
> _Savings Goals: -$500.00_

## Available Actions

| Action                       | Description                                    |
| ---------------------------- | ---------------------------------------------- |
| `list`                       | List all budget months with summaries          |
| `get`                        | Get detailed info for a specific month         |
| `list_money_movements`       | See category-level money movements for a month |
| `list_money_movement_groups` | See group-level money movements for a month    |

---

## API Reference

<!-- prettier-ignore -->
::: ynaa_mcp.tools.months.manage_months
    options:
      show_root_heading: true
      show_source: true
