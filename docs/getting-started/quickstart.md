# Quickstart

Once you have a [YNAB Personal Access Token](installation.md#get-a-ynab-personal-access-token), configure your MCP client to run the server.

## Configure your client

=== "Claude Desktop"

    Add the following to your `claude_desktop_config.json`:

    ```json
    {
      "mcpServers": {
        "ynab": {
          "command": "uvx",
          "args": ["ynab-mcp"],
          "env": {
            "YNAB_PAT": "your-personal-access-token"
          }
        }
      }
    }
    ```

    Replace `your-personal-access-token` with the token from the [installation step](installation.md#get-a-ynab-personal-access-token).

    See the [Configuration page](configuration.md) for file location details and additional options.

=== "Generic MCP Client"

    Run the server with your token as an environment variable:

    ```bash
    YNAB_PAT=your-personal-access-token uvx ynab-mcp
    ```

    Point your MCP client at the running server using its stdio transport.

??? info "New to MCP?"

    MCP clients connect to MCP servers over a standard protocol. Claude Desktop has
    built-in MCP support -- you just add the server configuration and it handles the rest.
    Other clients may require pointing at a running server process.

    [Learn more about MCP](https://modelcontextprotocol.io/) | [What is MCP?](what-is-mcp.md)

## Try it out

Once connected, try asking your AI assistant:

> **You:** Show me my budget summary.
>
> **Claude:** Your budget "My Budget" has 15 accounts with a total balance of $12,340.50. This month you've budgeted $4,200 across 28 categories, with $3,150 spent so far. Your Age of Money is 45 days.

Here are some other things to try:

- "How much did I spend on dining out last month?"
- "What categories are overspent?"
- "List my accounts and their balances"
- "Show me my scheduled transactions for this month"

The server handles authentication, rate limiting, and data formatting automatically. You just ask questions in natural language.

## What's available

YNAB MCP exposes three types of capabilities:

- **Tools** -- Read and write your YNAB data (budgets, accounts, categories, transactions, payees, months, scheduled transactions, cache management)
- **Prompts** -- Pre-built analysis and workflow templates (spending trends, budget health, debt payoff planning)
- **Resources** -- YNAB methodology knowledge that informs the assistant's advice (Four Rules, overspending, credit cards)

See the [User Guide](../user-guide/tools/index.md) for the full list of tools, prompts, and resources.

## Next steps

- [Configuration](configuration.md) -- Environment variables and client setup details
- [Tools overview](../user-guide/tools/index.md) -- All available tool domains
- [Analysis Prompts](../user-guide/prompts/analysis-prompts.md) -- Built-in budget analysis templates
