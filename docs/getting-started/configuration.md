# Configuration

Everything you need to connect YNAB MCP to your budget and your AI assistant.

## Environment Variables

| Variable   | Required | Description                                                                                                       |
| ---------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `YNAB_PAT` | Yes      | Your YNAB Personal Access Token. Get one from [YNAB Developer Settings](https://app.ynab.com/settings/developer). |

The server validates `YNAB_PAT` at startup and refuses to start with a clear error if the token is missing or invalid. It authenticates by calling the YNAB API's user endpoint, so an expired or revoked token will be caught immediately.

!!! warning "Keep your token secret"

    Your Personal Access Token provides **full access** to your YNAB account data -- every budget, account, transaction, and category. Treat it like a password:

    - Never commit it to version control
    - Never share it in chat or screenshots
    - Store it in your MCP client config or a secrets manager
    - Rotate it from [YNAB Developer Settings](https://app.ynab.com/settings/developer) if you suspect it was exposed

## Claude Desktop Configuration

Claude Desktop has built-in MCP support. Add the server to your `claude_desktop_config.json` file:

=== "uvx (recommended)"

    The simplest approach -- runs the latest published version without a local install:

    ```json
    {
      "mcpServers": {
        "ynab": {
          "command": "uvx",
          "args": ["--from", "you-need-an-advisor-mcp", "ynaa-mcp"],
          "env": {
            "YNAB_PAT": "your-personal-access-token"
          }
        }
      }
    }
    ```

=== "uv run (local development)"

    If you've cloned the repository and want to run your local copy:

    ```json
    {
      "mcpServers": {
        "ynab": {
          "command": "uv",
          "args": ["run", "ynaa-mcp"],
          "env": {
            "YNAB_PAT": "your-personal-access-token"
          }
        }
      }
    }
    ```

Replace `your-personal-access-token` with the token from [YNAB Developer Settings](https://app.ynab.com/settings/developer).

### Config file location

| Platform | Path                                                              |
| -------- | ----------------------------------------------------------------- |
| macOS    | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows  | `%APPDATA%\Claude\claude_desktop_config.json`                     |

!!! tip "Testing your connection"

    After saving the config, restart Claude Desktop. Then ask: **"Show me my budgets."** If the connection is working, Claude will call the `manage_budgets` tool and list your YNAB budgets.

## Other MCP Clients

Any MCP-compatible client can connect to YNAB MCP using the stdio transport. The generic configuration format is:

```json
{
  "command": "uvx",
  "args": ["--from", "you-need-an-advisor-mcp", "ynaa-mcp"],
  "env": {
    "YNAB_PAT": "your-personal-access-token"
  }
}
```

| Field     | Description                                                  |
| --------- | ------------------------------------------------------------ |
| `command` | The executable to run (`uvx` or `uv`)                        |
| `args`    | Command-line arguments passed to the executable              |
| `env`     | Environment variables -- `YNAB_PAT` is the only required one |

The server communicates over **stdio** (standard input/output), which is the default MCP transport. No network ports or URLs to configure.

## Server Options

YNAB MCP is designed to work out of the box with sensible defaults. There are no required configuration options beyond `YNAB_PAT`.

### Rate Limiting

The YNAB API enforces a limit of **200 requests per hour**. The server tracks request counts using a sliding window and throttles proactively at 190 requests (95% of the limit). You don't need to configure anything -- rate limiting is always active and automatic.

If the limit is approached, tools return a clear message with the number of seconds to wait before retrying.

### Budget Auto-Resolution

When you have **one budget**, the server selects it automatically. You can ask things like "list my accounts" without specifying which budget.

When you have **multiple budgets**, tools that need a budget will ask you to specify one by name or ID. The server supports fuzzy name matching, so "my budgt" will find "My Budget."

### Delta Caching

The server maintains a local cache for frequently accessed data like budget lists. YNAB's delta request mechanism (`server_knowledge`) lets the server fetch only changes since the last request, reducing API usage and improving response times. The cache is stored in memory and cleared when the server restarts.

You can manually clear the cache at any time by asking Claude to clear it -- this calls the `clear_cache` tool.
