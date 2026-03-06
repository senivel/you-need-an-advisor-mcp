# Category Tools

Categories are the heart of YNAB budgeting -- they're where you give every dollar a job. Category tools let you browse your budget structure, check balances and goal progress, create new categories, and set monthly budget amounts. If budgeting in YNAB is about answering "what does this money need to do?", categories are where you write those answers down.

Categories are organized into **category groups** (like "Monthly Bills", "Fun Money", "Savings Goals") that help you see the big picture. Each group contains individual categories (like "Rent", "Electric", "Internet" under "Monthly Bills").

## Usage Examples

> **You:** Show me my budget categories.
>
> **Claude** calls `manage_categories` with action `list` and responds:
>
> _Monthly Bills:_
> _- Rent -- Budgeted: $1,500.00 | Activity: -$1,500.00 | Balance: $0.00_
> _- Electric -- Budgeted: $120.00 | Activity: -$95.40 | Balance: $24.60_
> _- Internet -- Budgeted: $75.00 | Activity: $0.00 | Balance: $75.00_
>
> _Fun Money:_
> _- Dining Out -- Budgeted: $200.00 | Activity: -$142.30 | Balance: $57.70_
> _- Entertainment -- Budgeted: $100.00 | Activity: -$35.99 | Balance: $64.01_

> **You:** How's my Groceries category doing?
>
> **Claude** calls `manage_categories` with action `get` and responds:
>
> _Category: Groceries_
> _Budgeted: $600.00_
> _Activity: -$423.17_
> _Balance: $176.83_
> _Goal: Monthly Funding -- Target: $600.00 (71% complete)_

> **You:** Set my Dining Out budget to $250 for this month.
>
> **Claude** calls `manage_categories` with action `set_month_budget`, converting dollars to milliunits:
>
> _Updated Dining Out for March 2026:_
> _Budgeted: $250.00_

> **You:** Create a new category called "Concert Fund" in my Savings Goals group.
>
> **Claude** calls `manage_categories` with action `create`:
>
> _Category created: Concert Fund_
> _Group: Savings Goals_

## Available Actions

| Action             | Description                                          |
| ------------------ | ---------------------------------------------------- |
| `list`             | List all categories grouped by category group        |
| `get`              | Get details for a specific category (with goal info) |
| `create`           | Create a new category in a group                     |
| `update`           | Update a category's name or note                     |
| `create_group`     | Create a new category group                          |
| `update_group`     | Rename a category group                              |
| `set_month_budget` | Set the budgeted amount for a category in a month    |

---

## API Reference

<!-- prettier-ignore -->
::: ynab_mcp.tools.categories.manage_categories
    options:
      show_root_heading: true
      show_source: true
