# You Need an Advisor MCP

**Not just API coverage -- a YNAB budgeting advisor powered by embedded methodology knowledge.**

An [MCP](https://modelcontextprotocol.io/) server that connects AI assistants like Claude to your [YNAB](https://www.ynab.com/) budget. Ask questions about your finances in natural language and get answers backed by real data from the YNAB API, informed by YNAB's budgeting methodology.

![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Features

- **Full YNAB API coverage** -- Budgets, accounts, categories, transactions, payees, months, scheduled transactions
- **YNAB methodology built-in** -- Embedded knowledge of the Four Rules, overspending, credit cards, reconciliation, and Age of Money
- **Analysis & workflow prompts** -- Spending trends, budget health, debt payoff planning, and more
- **Secure** -- Your Personal Access Token stays on your machine; no data stored or forwarded

## Quick start

**1.** Get a [YNAB Personal Access Token](https://app.ynab.com/settings/developer)

**2.** Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ynab": {
      "command": "uvx",
      "args": ["you-need-an-advisor-mcp"],
      "env": {
        "YNAB_PAT": "your-token-here"
      }
    }
  }
}
```

**3.** Ask Claude about your budget.

## Documentation

Full documentation: **[senivel.github.io/you-need-an-advisor-mcp](https://senivel.github.io/you-need-an-advisor-mcp/)**

## Links

- [Contributing](https://senivel.github.io/you-need-an-advisor-mcp/contributing/)
- [Changelog](https://senivel.github.io/you-need-an-advisor-mcp/contributing/changelog/)
- [License](LICENSE)
