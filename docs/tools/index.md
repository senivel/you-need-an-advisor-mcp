# Tools Reference

YNAB MCP exposes a set of **tools** that AI assistants like Claude can call on your behalf. You interact with these tools through natural language -- ask Claude what you want to know about your budget, and it picks the right tool automatically.

## Available Tool Domains

| Domain           | Description                                                                        | Page                            |
| ---------------- | ---------------------------------------------------------------------------------- | ------------------------------- |
| **Budget Tools** | List budgets, get budget details, manage accounts, categories, and monthly budgets | [Budget Tools](budget-tools.md) |

!!! note "More tools coming soon"
Budget tools cover the foundation implemented in Phase 1. Future phases will add tools for transactions, payees, scheduled transactions, and reporting.

??? info "New to MCP?"
MCP (Model Context Protocol) is a standard that lets AI assistants call external tools. You never call these tools directly -- instead, you ask Claude something like _"Show me my budgets"_ and Claude decides which tool to use, calls it, and formats the response for you.

    Think of it like a waiter at a restaurant: you tell the waiter what you want (natural language), and the waiter communicates with the kitchen (MCP tools) on your behalf. You never need to know the kitchen's internal API.
