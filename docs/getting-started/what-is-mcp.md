# What is MCP?

If you use YNAB (You Need A Budget) and want AI to help with your budgeting, you're in the right place. This page explains what MCP is and why it matters for your budget.

## The Short Version

**MCP** stands for **Model Context Protocol**. It's a standard that lets AI assistants like Claude interact with external services -- in this case, your YNAB budget.

Think of it this way: without MCP, Claude can only talk _about_ budgeting in general terms. With MCP, Claude can actually _see_ your budget, read your transactions, analyze your spending, and help you make real decisions with your real numbers.

## How It Works

The setup is straightforward:

1. **You install the YNAB MCP server** -- a small program that runs on your computer
2. **You configure your AI client** (like Claude Desktop) to connect to it
3. **You provide a YNAB Personal Access Token** so the server can read your budget data
4. **You talk to Claude naturally** -- it calls YNAB tools behind the scenes

```
You: "How much did I spend on dining out last month?"

     [Claude] ---> [YNAB MCP Server] ---> [YNAB API]
                                      <---
              <---
Claude: "You spent $342.17 on Dining Out in February..."
```

You never interact with the MCP server directly. You just talk to Claude, and it handles the rest.

## What Can It Do?

With YNAB MCP, Claude becomes a budgeting assistant that knows your actual numbers:

- **Budget overview** -- See all your budgets, accounts, and balances at a glance
- **Spending analysis** -- Ask about spending trends, category breakdowns, and month-over-month changes
- **Transaction management** -- Create, search, update, and categorize transactions through conversation
- **Category budgeting** -- Set monthly budget amounts, check category balances, track goal progress
- **YNAB methodology guidance** -- Get coaching on Age of Money, handling overspending, debt payoff strategies, and more
- **Recurring transactions** -- View and manage scheduled transactions and upcoming bills
- **Month summaries** -- Review income, budgeted amounts, and activity for any month

## Beyond Just Data Access

What makes this different from simply reading the YNAB API? The server includes built-in **YNAB methodology knowledge** -- guides on topics like the Four Rules, handling credit card debt, reconciliation workflows, and building an emergency fund. When Claude helps you with your budget, it draws on both your real data _and_ YNAB best practices.

It's not just an API wrapper. It's a budgeting advisor that speaks YNAB.

## Ready to Get Started?

- [Installation](installation.md) -- Install the server in under a minute
- [Quickstart](../getting-started/quickstart.md) -- Your first conversation with YNAB MCP
- [Configuration](configuration.md) -- Set up your API token and client
