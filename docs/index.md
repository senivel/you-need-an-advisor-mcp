# YNAB MCP

An MCP server that gives AI assistants like Claude direct access to your [YNAB](https://www.ynab.com/) budget data -- and the knowledge to help you use it well. Ask questions about your finances in natural language and get answers backed by real data from the YNAB API, informed by YNAB's budgeting methodology.

## Not just API coverage -- a budgeting advisor

YNAB MCP doesn't just read and write your budget data. It comes with built-in knowledge of YNAB's methodology -- the Four Rules, how to handle overspending, credit card management, and more. When you ask Claude for help with your budget, you get advice that's grounded in both your real data and proven budgeting principles.

## Features

- **Full YNAB API coverage** -- Budgets, accounts, categories, transactions, payees, months, and scheduled transactions
- **YNAB methodology knowledge** -- Built-in resources covering the Four Rules, overspending, credit cards, reconciliation, and age of money
- **Analysis prompts** -- Spending trends, budget health checks, savings analysis, and more
- **Workflow guides** -- Step-by-step processes for debt payoff, budget setup, and financial reviews
- **Automatic budget resolution** -- If you have one budget, it's selected automatically; no need to specify an ID every time
- **Proactive rate limiting** -- Stays within YNAB's 200 requests/hour limit automatically
- **Milliunit conversion** -- All monetary values are returned in dollars, not YNAB's internal milliunit format
- **Structured error handling** -- Errors return clear, actionable messages instead of raw exceptions

??? info "New to MCP?"

    MCP (Model Context Protocol) is an open standard that lets AI assistants like Claude
    connect to external data sources and tools. This server exposes your YNAB budget data
    as MCP "tools" that an assistant can call on your behalf -- you just ask in natural language.

    [Learn more about MCP](https://modelcontextprotocol.io/)

## Get Started

Ready to set up? Head to [Installation](getting-started/installation.md) to get your token and install, then follow the [Quickstart](getting-started/quickstart.md) to connect your first AI assistant.
