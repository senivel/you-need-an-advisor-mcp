# Tools

YNAB MCP provides **8 tool domains** that cover every aspect of your YNAB budget. AI assistants like Claude call these tools automatically when you ask budget-related questions -- you never need to remember tool names or parameters.

## Available Tools

| Tool                            | Description                                                           | Page                                                          |
| ------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------- |
| **Budget Tools**                | List budgets, get details, check user info                            | [Budget Tools](budget-tools.md)                               |
| **Account Tools**               | List, view, and create accounts (on-budget and tracking)              | [Account Tools](account-tools.md)                             |
| **Category Tools**              | Browse categories, manage groups, set monthly budgets, track goals    | [Category Tools](category-tools.md)                           |
| **Transaction Tools**           | Create, search, update, delete, batch import, and filter transactions | [Transaction Tools](transaction-tools.md)                     |
| **Payee Tools**                 | List payees, rename for consistency, view locations                   | [Payee Tools](payee-tools.md)                                 |
| **Month Tools**                 | View monthly summaries, income, activity, and money movements         | [Month Tools](month-tools.md)                                 |
| **Scheduled Transaction Tools** | Manage recurring and upcoming transactions                            | [Scheduled Transaction Tools](scheduled-transaction-tools.md) |
| **Cache Tools**                 | Clear cached data when you need fresh results                         | [Cache Tools](cache-tools.md)                                 |

## How It Works

Each tool uses an **action-based dispatch pattern**. For example, the Budget Tools accept actions like `list`, `get`, and `get_user`. Claude picks the right action based on what you ask. You just talk naturally:

> "Show me my budgets" --> `manage_budgets` with action `list`
> "How much is in my Groceries category?" --> `manage_categories` with action `get`
> "I spent $50 at the grocery store" --> `manage_transactions` with action `create`

**Budget resolution** is automatic: if you have one budget, tools use it without asking. If you have multiple, Claude will match by name or ask which one you mean.

<!-- prettier-ignore-start -->
??? info "New to MCP?"
    MCP (Model Context Protocol) is a standard that lets AI assistants call external tools. You never call these tools directly -- instead, you ask Claude something like _"Show me my budgets"_ and Claude decides which tool to use, calls it, and formats the response for you.

    Think of it like a waiter at a restaurant: you tell the waiter what you want (natural language), and the waiter communicates with the kitchen (MCP tools) on your behalf. You never need to know the kitchen's internal API.

    Learn more: [What is MCP?](../../getting-started/what-is-mcp.md)
<!-- prettier-ignore-end -->
