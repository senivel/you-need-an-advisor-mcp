# YNAB MCP

MCP server for You Need A Budget -- access your YNAB data through AI assistants.

![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![CI: coming soon](https://img.shields.io/badge/CI-coming%20soon-lightgrey)

## What is this?

An [MCP](https://modelcontextprotocol.io/) server that lets AI assistants like Claude interact with your YNAB budget. Ask questions about your finances, manage transactions, and analyze spending patterns through natural language.

## Features

- Personal Access Token authentication with startup validation
- Proactive rate limiting (200 req/hr YNAB API limit)
- Automatic budget resolution (single budget auto-selected)
- Milliunit-to-dollar conversion on all monetary values
- Structured error handling with actionable messages
- All logging to stderr (stdout reserved for MCP transport)

### Coming Soon

- Transaction CRUD and filtering
- Scheduled transactions and payees
- Delta-request caching
- Spending analytics and bulk operations

## Quickstart

**Prerequisites:** Python 3.13+, [uv](https://docs.astral.sh/uv/), a [YNAB Personal Access Token](https://api.ynab.com/#personal-access-tokens)

Add this to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ynab": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ynab-mcp", "ynab-mcp"],
      "env": {
        "YNAB_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

Replace `/path/to/ynab-mcp` with the actual path to your clone, and `your-token-here` with your YNAB Personal Access Token.

## Documentation

Full documentation: [senivel.github.io/ynab-mcp](https://senivel.github.io/ynab-mcp/)

> Documentation site will be live after Phase 8 (CI/CD). For now, build locally with `uv run --group docs mkdocs serve`.

## License

MIT License -- see [LICENSE](LICENSE) for details.
