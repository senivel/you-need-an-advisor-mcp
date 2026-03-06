Enter transactions into the budget.

1. Read the accounts resource at `ynab://budgets/{budget_id}/accounts` to know the available accounts.
2. Read the categories resource at `ynab://budgets/{budget_id}/categories` to know the available categories.
3. Ask the user for transaction details: date, payee, amount, account, category, and memo.
4. Use the `manage_transactions` tool with action="create" to enter each transaction.
5. Confirm the transaction details after each entry.
6. Ask if there are more transactions to enter.
