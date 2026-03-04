# Budget Tools

Budget tools let you view and manage your YNAB budgets, accounts, and categories through natural conversation with Claude.

## Usage Examples

You don't call these tools directly. Instead, ask Claude naturally and it picks the right tool:

### Listing Budgets

> **You:** Show me my budgets.
>
> **Claude** calls `list_budgets` and responds with something like:
>
> _2 budgets found:_
> _- My Budget (Last modified: 2026-03-01)_
> _- Vacation Fund (Last modified: 2026-02-15)_

### Budget Details

> **You:** What's in my main budget?
>
> **Claude** calls `get_budget` with fuzzy name matching and responds:
>
> _Budget: My Budget_
> _First month: 2024-01-01_
> _Last month: 2026-04-01_
> _Currency: USD_

### Working with Accounts

> **You:** List my accounts.
>
> **Claude** calls `get_accounts` and shows your open accounts with balances formatted in dollars.

> **You:** Create a new savings account called Emergency Fund with $1,000.
>
> **Claude** calls `create_account`, converting your dollar amount to YNAB milliunits behind the scenes.

### Managing Categories

> **You:** Show me my budget categories.
>
> **Claude** calls `get_categories` and displays them grouped by category group, with budgeted, activity, and balance amounts.

> **You:** Set my Groceries budget to $500 for this month.
>
> **Claude** calls `month_category_budget` with the dollar amount, handling the milliunit conversion automatically.

??? info "New to MCP?"
These tools are called by Claude automatically when you ask budget-related questions. You never need to remember tool names or parameters -- just describe what you want in plain English.

    **Budget resolution** is automatic too: if you only have one budget, tools use it without asking. If you have multiple budgets, Claude will ask which one you mean or match by name.

---

## API Reference

Auto-generated reference from source code docstrings.

### Budget Operations

::: ynab_mcp.server.list_budgets
options:
show_root_heading: true
show_source: true

::: ynab_mcp.server.get_budget
options:
show_root_heading: true
show_source: true

### User

::: ynab_mcp.server.get_user
options:
show_root_heading: true
show_source: true

### Account Operations

::: ynab_mcp.server.get_accounts
options:
show_root_heading: true
show_source: true

::: ynab_mcp.server.get_account
options:
show_root_heading: true
show_source: true

::: ynab_mcp.server.create_account
options:
show_root_heading: true
show_source: true

### Category Operations

::: ynab_mcp.server.get_categories
options:
show_root_heading: true
show_source: true

::: ynab_mcp.server.get_category
options:
show_root_heading: true
show_source: true

::: ynab_mcp.server.manage_category
options:
show_root_heading: true
show_source: true

::: ynab_mcp.server.manage_category_group
options:
show_root_heading: true
show_source: true

### Monthly Budget Operations

::: ynab_mcp.server.month_category_budget
options:
show_root_heading: true
show_source: true
