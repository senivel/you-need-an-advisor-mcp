# Budget Resolver

Most YNAB users have a single budget. The budget resolver automatically selects it, so users don't need to specify a budget ID for every request.

## How Resolution Works

Every tool that operates on a budget calls `resolve_budget()` before making API requests. Resolution follows three paths:

1. **No identifier provided:** If you have exactly one budget, it's selected automatically with an info message like _"Using budget 'My Budget' (only budget found)"_. If you have multiple budgets, the tool returns an error listing available budgets.

2. **UUID provided:** Exact match against known budget IDs. No API call needed beyond the initial budget list fetch.

3. **Name provided:** Fuzzy matching using `difflib.SequenceMatcher` with a similarity threshold of 60%. This handles typos and partial names -- asking for _"my budgt"_ will match _"My Budget"_.

## Why This Exists

Without auto-resolution, every single tool call would require a budget ID parameter. For the majority of users with one budget, this would mean:

- Extra prompts from Claude asking "which budget?"
- Users needing to look up and paste UUIDs
- A worse conversational experience

The resolver makes the common case (one budget) effortless while still supporting the multi-budget case gracefully.

## API Reference

::: ynab_mcp.budget_resolver
options:
show_root_heading: true
show_source: true
members_order: source
