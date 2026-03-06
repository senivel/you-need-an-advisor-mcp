# Installation

## Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** -- Python package and project manager
- **YNAB Personal Access Token** -- Required for API authentication

## Get a YNAB Personal Access Token

1. Log in to [YNAB](https://app.ynab.com/)
2. Go to **Account Settings** > **Developer Settings** ([direct link](https://app.ynab.com/settings/developer))
3. Click **New Token** and follow the prompts
4. Copy the token -- you'll need it for configuration

!!! warning

    Keep your token secret. It provides full access to your YNAB account data.

## Install

This is an MCP server, not a standalone CLI. It's meant to be configured in an MCP client (like Claude Desktop). There are two ways to make it available:

**As a project dependency:**

```bash
uv add ynab-mcp
```

**Run directly without installing:**

```bash
uvx ynab-mcp
```

See the [Quickstart](quickstart.md) for how to configure your MCP client to use the server.
