# Budget Tools

Your budget is the foundation of everything in YNAB. Budget tools give you a bird's-eye view of your financial world -- listing your budgets, checking their details, and verifying your YNAB account info. Whether you manage one household budget or separate budgets for different goals, these tools are your starting point.

Most other tools need to know _which_ budget to work with. If you only have one, it's selected automatically. If you have multiple, Claude will ask or match by name.

<!-- prettier-ignore-start -->
??? tip "Budget Resolution"
    When you say something like "show me my Groceries category", the server needs to know which budget to look in. Here's how it works:

    - **One budget?** It's selected automatically -- you never need to specify it.
    - **Multiple budgets?** Claude will try to match by name (fuzzy matching), or ask you to clarify.
    - **`last-used` shortcut:** Most tools default to `last-used`, which picks the budget from YNAB's "last used" setting.

    This means most conversations just work without you ever thinking about budget selection.
<!-- prettier-ignore-end -->

## Usage Examples

> **You:** Show me my budgets.
>
> **Claude** calls `manage_budgets` with action `list` and responds:
>
> _2 budgets found:_
> _- My Budget (Last modified: 2026-03-01)_
> _- Vacation Fund (Last modified: 2026-02-15)_

> **You:** What's in my main budget?
>
> **Claude** calls `manage_budgets` with action `get` and fuzzy name matching:
>
> _Budget: My Budget_
> _First month: 2024-01-01_
> _Last month: 2026-04-01_
> _Currency: USD_
> _Date format: MM/DD/YYYY_

> **You:** What YNAB account am I using?
>
> **Claude** calls `manage_budgets` with action `get_user` and responds:
>
> _User: jane@example.com_
> _ID: abc123-def456_

> **You:** Tell me about my Vacation Fund budget.
>
> **Claude** calls `manage_budgets` with action `get` and name matching:
>
> _Budget: Vacation Fund_
> _First month: 2025-06-01_
> _Last month: 2026-06-01_
> _Currency: USD_
> _Number of accounts: 2_
> _Number of categories: 8_
>
> _This budget has 12 months of history._

<!-- prettier-ignore-start -->
??? info "New to MCP?"
    These tools are called by Claude automatically when you ask budget-related questions. You never need to remember tool names or parameters -- just describe what you want in plain English.

    **Budget resolution** is automatic too: if you only have one budget, tools use it without asking. If you have multiple budgets, Claude will ask which one you mean or match by name.
<!-- prettier-ignore-end -->

## Available Actions

| Action     | Description                               |
| ---------- | ----------------------------------------- |
| `list`     | List all budgets on your YNAB account     |
| `get`      | Get detailed info about a specific budget |
| `get_user` | Get your YNAB user/account info           |

## Common Patterns

**Starting a conversation:** Most budget conversations begin with "show me my budgets" or "how's my budget doing?" -- Claude will list budgets or get details for your default budget.

**Multiple budgets:** If you maintain separate budgets (e.g., personal and business, or a vacation fund), you can refer to them by name. Claude uses fuzzy matching, so "vacation" will match "Vacation Fund".

**Budget details:** The `get` action returns metadata like date range, currency, and format settings. For actual spending data, use [Month Tools](month-tools.md). For account balances, use [Account Tools](account-tools.md).

---

## API Reference

<!-- prettier-ignore -->
::: ynab_mcp.tools.budgets.manage_budgets
    options:
      show_root_heading: true
      show_source: true
