# Tools

YNAB MCP exposes a set of **tools** that AI assistants like Claude can call on your behalf. You interact with these tools through natural language -- ask Claude what you want to know about your budget, and it picks the right tool automatically.

## Available Tools

| Tool                            | Description                                                   | Page                                                          |
| ------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------- |
| **Budget Tools**                | List budgets, get details, user info                          | [Budget Tools](budget-tools.md)                               |
| **Account Tools**               | List, view, and create accounts                               | [Account Tools](account-tools.md)                             |
| **Category Tools**              | Browse categories, manage groups, set monthly budgets         | [Category Tools](category-tools.md)                           |
| **Transaction Tools**           | Create, search, update, delete, and batch-manage transactions | [Transaction Tools](transaction-tools.md)                     |
| **Payee Tools**                 | List payees, update names, view locations                     | [Payee Tools](payee-tools.md)                                 |
| **Month Tools**                 | View monthly summaries, money movements                       | [Month Tools](month-tools.md)                                 |
| **Scheduled Transaction Tools** | Manage recurring and upcoming transactions                    | [Scheduled Transaction Tools](scheduled-transaction-tools.md) |
| **Cache Tools**                 | Clear the local cache when needed                             | [Cache Tools](cache-tools.md)                                 |

??? info "New to MCP?"
MCP (Model Context Protocol) is a standard that lets AI assistants call external tools. You never call these tools directly -- instead, you ask Claude something like _"Show me my budgets"_ and Claude decides which tool to use, calls it, and formats the response for you.

    Think of it like a waiter at a restaurant: you tell the waiter what you want (natural language), and the waiter communicates with the kitchen (MCP tools) on your behalf. You never need to know the kitchen's internal API.
