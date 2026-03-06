# Budget Tools

Budget tools let you view and manage your YNAB budgets, accounts, and categories through natural conversation with Claude.

## Usage Examples

You don't call these tools directly. Instead, ask Claude naturally and it picks the right tool:

### Listing Budgets

> **You:** Show me my budgets.
>
> **Claude** calls `manage_budgets` with action `list` and responds with something like:
>
> _2 budgets found:_
> _- My Budget (Last modified: 2026-03-01)_
> _- Vacation Fund (Last modified: 2026-02-15)_

### Budget Details

> **You:** What's in my main budget?
>
> **Claude** calls `manage_budgets` with action `get` and fuzzy name matching:
>
> _Budget: My Budget_
> _First month: 2024-01-01_
> _Last month: 2026-04-01_
> _Currency: USD_

### Working with Accounts

> **You:** List my accounts.
>
> **Claude** calls `manage_accounts` with action `list` and shows your open accounts with balances formatted in dollars.

> **You:** Create a new savings account called Emergency Fund with $1,000.
>
> **Claude** calls `manage_accounts` with action `create`, converting your dollar amount to YNAB milliunits behind the scenes.

### Managing Categories

> **You:** Show me my budget categories.
>
> **Claude** calls `manage_categories` with action `list` and displays them grouped by category group, with budgeted, activity, and balance amounts.

> **You:** Set my Groceries budget to $500 for this month.
>
> **Claude** calls `manage_categories` with action `set_month_budget`, handling the milliunit conversion automatically.

??? info "New to MCP?"
These tools are called by Claude automatically when you ask budget-related questions. You never need to remember tool names or parameters -- just describe what you want in plain English.

    **Budget resolution** is automatic too: if you only have one budget, tools use it without asking. If you have multiple budgets, Claude will ask which one you mean or match by name.

---

## API Reference

Auto-generated reference from source code docstrings.

::: ynab_mcp.tools.budgets.manage_budgets
options:
show_root_heading: true
show_source: true
