# YNAB MCP

An MCP server that gives AI assistants like Claude direct access to your [YNAB](https://www.ynab.com/) budget data. Ask questions about your finances in natural language and get answers backed by real data from the YNAB API.

## Features

- **Authentication with rate limiting** -- Authenticates via Personal Access Token and proactively throttles requests to stay within YNAB's 200 requests/hour limit
- **Budget auto-resolution** -- If you have one budget, it's selected automatically; no need to specify an ID every time
- **Milliunit conversion** -- All monetary values are returned in dollars, not YNAB's internal milliunit format
- **Structured error handling** -- Errors return clear, actionable messages instead of raw exceptions
- **Budget and account tools** -- List budgets, view accounts, explore categories and category groups
- **Category management** -- Create and update categories, set goals, manage monthly budgets

## Coming Soon

Future phases will add:

- Transaction CRUD and filtering (Phase 3)
- Scheduled transactions, payees, and months (Phase 4)
- Delta-request caching and MCP resources/prompts (Phase 5)
- Spending analysis, trends, and bulk operations (Phase 6)

??? info "New to MCP?"

    MCP (Model Context Protocol) is an open standard that lets AI assistants like Claude
    connect to external data sources and tools. This server exposes your YNAB budget data
    as MCP "tools" that an assistant can call on your behalf -- you just ask in natural language.

    [Learn more about MCP](https://modelcontextprotocol.io/)

## YNAB API Concepts

This server wraps the [YNAB API](https://api.ynab.com/). A few concepts are useful to know:

- **Milliunits** -- YNAB stores amounts as milliunits (1 dollar = 1,000 milliunits). This server converts automatically, so you always see dollar amounts.
- **`server_knowledge`** -- YNAB supports delta requests to fetch only changes since a previous call. This will be used for caching in Phase 5.
- **Rate limits** -- The YNAB API allows 200 requests per hour. The server tracks usage and throttles proactively.

## Get Started

Ready to set up? Head to [Installation](installation.md) to get your token and install, then follow the [Quickstart](quickstart.md) to connect your first AI assistant.
