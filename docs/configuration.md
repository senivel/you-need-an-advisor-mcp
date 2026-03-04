# Configuration

## Environment Variables

| Variable   | Required | Description                                                                                                       |
| ---------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `YNAB_PAT` | Yes      | Your YNAB Personal Access Token. Get one from [YNAB Developer Settings](https://app.ynab.com/settings/developer). |

The server validates `YNAB_PAT` at startup and refuses to start with a clear error if the token is missing or invalid.

## Rate Limiting

The YNAB API enforces a limit of **200 requests per hour**. The server tracks request counts and throttles proactively:

- Requests are counted using a sliding window
- When approaching the limit, the server slows down automatically
- If the limit is hit, tools return a clear retry message with the wait time

You don't need to configure anything -- rate limiting is built in and always active.

## Budget Auto-Resolution

When you have **one budget**, the server selects it automatically. You can call tools like "list my accounts" without specifying which budget.

When you have **multiple budgets**, tools that require a budget will ask you to specify which one by name or ID. You can list your budgets first to see what's available.
