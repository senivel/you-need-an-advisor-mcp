# Quickstart

Once you have a [YNAB Personal Access Token](installation.md#get-a-ynab-personal-access-token), configure your MCP client to run the server.

## Configure Your Client

=== "Claude Desktop"

    Add the following to your `claude_desktop_config.json`:

    ```json
    {
      "mcpServers": {
        "ynab": {
          "command": "uv",
          "args": ["run", "ynab-mcp"],
          "env": {
            "YNAB_PAT": "your-personal-access-token"
          }
        }
      }
    }
    ```

    Replace `your-personal-access-token` with the token from the [installation step](installation.md#get-a-ynab-personal-access-token).

=== "Generic MCP Client"

    Run the server with your token as an environment variable:

    ```bash
    YNAB_PAT=your-personal-access-token uv run ynab-mcp
    ```

    Point your MCP client at the running server using its stdio transport.

??? info "New to MCP?"

    MCP clients connect to MCP servers over a standard protocol. Claude Desktop has
    built-in MCP support -- you just add the server configuration and it handles the rest.
    Other clients may require pointing at a running server process.

    [Learn more about MCP](https://modelcontextprotocol.io/)

## Try It Out

Once connected, try asking your AI assistant:

- "Show me my budgets"
- "What's my budget summary?"
- "List my accounts"
- "What categories do I have?"
- "How much is budgeted for groceries this month?"

The server handles authentication, rate limiting, and data formatting automatically. You just ask questions in natural language.

## Next Steps

- [Configuration](configuration.md) -- Environment variables and rate limiting details
- [Tools](../user-guide/tools/index.md) -- Full list of available tools
