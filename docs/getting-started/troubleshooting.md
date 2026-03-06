# Troubleshooting and FAQ

Running into issues? This page covers the most common problems and how to fix them.

## Common Issues

!!! failure "YNAB_PAT environment variable is required"

    **What happened:** The server started but can't find your YNAB Personal Access Token.

    **The fix:** The token must be set in your **MCP client configuration**, not in your shell profile. The server reads it from the environment passed by the client.

    === "Claude Desktop"

        Edit your `claude_desktop_config.json` and make sure `YNAB_PAT` is in the `env` block:

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

    === "Other MCP Clients"

        Check your client's documentation for how to set environment variables for MCP servers. The variable name is `YNAB_PAT`.

    **Where to get a token:** Go to [YNAB Developer Settings](https://app.ynab.com/settings/developer) and create a Personal Access Token.

!!! failure "401 Unauthorized"

    **What happened:** Your YNAB Personal Access Token is invalid or expired.

    **The fix:**

    1. Go to [YNAB Developer Settings](https://app.ynab.com/settings/developer)
    2. Check if your token is still listed and active
    3. If expired or revoked, create a new one
    4. Update the token in your MCP client configuration
    5. Restart your MCP client

    !!! tip
        YNAB tokens don't expire on their own, but they can be revoked manually. If you regenerated your token, make sure to update it everywhere.

!!! failure "404 Budget not found"

    **What happened:** You referenced a budget that doesn't exist or the name doesn't match.

    **The fix:** Ask Claude to list your budgets first:

    > **You:** Show me my budgets.

    This returns the exact names and IDs. Then use the correct name in your next request. Budget matching is fuzzy but not magic -- "My Budget" won't match "Household Budget" unless there's only one budget.

    Common causes:

    - Typo in the budget name
    - Budget was deleted in YNAB
    - Using a budget ID that belongs to a different YNAB account

!!! failure "429 Too Many Requests (Rate Limiting)"

    **What happened:** You've hit YNAB's API rate limit.

    **Background:** YNAB allows **200 requests per hour** per access token. The YNAB MCP server has a built-in rate limiter that tracks your usage and will warn you when you're approaching the limit.

    **The fix:**

    - Wait for the rate limit window to reset (resets hourly)
    - The server caches budget data to minimize API calls -- avoid clearing the cache unnecessarily
    - If you're consistently hitting limits, space out large operations (like batch transaction imports)

    !!! tip
        Most normal conversations use only a handful of API calls. Rate limiting typically only becomes an issue during bulk operations or rapid-fire queries.

!!! failure "Claude Desktop can't find the server"

    **What happened:** Claude Desktop shows no YNAB tools available, or reports a connection error.

    **The fix:**

    === "macOS"

        1. Check your config file location:
           ```
           ~/Library/Application Support/Claude/claude_desktop_config.json
           ```

        2. Verify `uvx` is on your PATH:
           ```bash
           which uvx
           ```
           If not found, install `uv` first: `curl -LsSf https://astral.sh/uv/install.sh | sh`

        3. Restart Claude Desktop completely (quit and reopen, not just close the window)

    === "Windows"

        1. Check your config file location:
           ```
           %APPDATA%\Claude\claude_desktop_config.json
           ```

        2. Verify `uvx` is on your PATH:
           ```
           where uvx
           ```
           If not found, install `uv` first: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

        3. Restart Claude Desktop completely

    **Common config mistakes:**

    - Trailing comma after the last entry in JSON (JSON doesn't allow this)
    - Wrong path to `uvx` -- use the full path if it's not on your system PATH
    - Missing quotes around string values

!!! failure "Server starts but no tools appear"

    **What happened:** The MCP server process is running but your AI client doesn't show any YNAB tools.

    **The fix:**

    1. **Check MCP client logs** -- most clients have a way to view MCP connection logs. In Claude Desktop, check the developer console or log files.

    2. **Verify your config JSON syntax** -- a single misplaced comma or missing bracket will silently break the config:
       ```bash
       # Quick JSON syntax check (macOS/Linux)
       python3 -c "import json; json.load(open('path/to/claude_desktop_config.json'))"
       ```

    3. **Try running the server manually** to see if it starts:
       ```bash
       uvx you-need-an-advisor-mcp
       ```
       If this errors, the issue is with the server installation, not the client config.

    4. **Restart the MCP client** after any config changes -- most clients don't hot-reload MCP configurations.

!!! failure "Stale data after making changes in YNAB"

    **What happened:** You made changes in the YNAB app or website, but Claude still shows old data.

    **The fix:** The server caches your budget list to reduce API calls. Ask Claude to clear the cache:

    > **You:** Clear the YNAB cache.

    This forces fresh data on the next request. Transaction and category data is fetched fresh each time, so this mainly affects budget list lookups.

## Still Stuck?

If your issue isn't listed here:

1. **Check the [GitHub Issues](https://github.com/senivel/you-need-an-advisor-mcp/issues)** -- someone may have already reported and resolved the same problem
2. **Open a new issue** with:
   - Your operating system
   - How you installed the server (`uvx`, `uv run`, etc.)
   - Which MCP client you're using
   - The full error message
   - Steps to reproduce the problem
