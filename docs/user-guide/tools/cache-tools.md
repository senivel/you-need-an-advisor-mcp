# Cache Tools

The YNAB MCP server caches your budget list to minimize API calls and stay within YNAB's rate limits. Cache tools let you clear this cache when you need fresh data -- for example, after creating a new budget in the YNAB app or if something looks stale.

Most of the time you won't need to touch the cache. Transaction and category data is fetched fresh on each request. The cache primarily covers the budget list lookup, which changes infrequently.

## Usage Examples

> **You:** Clear the YNAB cache.
>
> **Claude** calls `clear_cache` and responds:
>
> _All caches cleared._

> **You:** I just created a new budget in YNAB but it's not showing up.
>
> **Claude** calls `clear_cache` to refresh, then `manage_budgets` with action `list`:
>
> _Cache cleared. Here are your current budgets:_
> _3 budgets found:_
> _- My Budget (Last modified: 2026-03-06)_
> _- Vacation Fund (Last modified: 2026-02-15)_
> _- New Side Project (Last modified: 2026-03-06)_

## When to Clear the Cache

- You created or deleted a budget in the YNAB app or website
- Budget names or settings were changed outside of MCP
- You're seeing budget list data that doesn't match what's in YNAB

You can clear the cache for a specific budget by ID, or clear everything at once.

---

## API Reference

<!-- prettier-ignore -->
::: ynab_mcp.tools.cache.clear_cache
    options:
      show_root_heading: true
      show_source: true
