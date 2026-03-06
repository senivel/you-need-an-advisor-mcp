# Transaction Tools

Transactions are the individual money movements that make up your budget's story. Transaction tools give you full control -- creating new transactions, searching and filtering existing ones, updating details, deleting mistakes, and even batch operations for importing or bulk updates. This is the most powerful tool in the set, and the one you'll likely use most often.

Every transaction in YNAB has a **cleared state** that tracks its journey:

- **Uncleared** `[U]` -- Entered but not yet confirmed by the bank
- **Cleared** `[C]` -- Confirmed to match your bank statement
- **Reconciled** `[R]` -- Locked in after reconciliation (no further edits)

## Usage Examples

> **You:** Show me my recent transactions.
>
> **Claude** calls `manage_transactions` with action `list` and responds:
>
> _10 most recent transactions:_
> _- 2026-03-05 | Whole Foods | -$87.32 | Groceries [C]_
> _- 2026-03-04 | Shell Gas | -$42.00 | Transportation [U]_
> _- 2026-03-03 | Spotify | -$15.99 | Subscriptions [C]_
> _- 2026-03-01 | Employer Inc | $3,200.00 | Income [R]_

> **You:** I spent $45 at Target on household supplies today.
>
> **Claude** calls `manage_transactions` with action `create`:
>
> _Transaction created:_
> _- 2026-03-06 | Target | -$45.00 | Household Supplies [U]_

> **You:** Show me all dining transactions from last month.
>
> **Claude** calls `manage_transactions` with action `list` with category and date filters:
>
> _8 transactions in Dining Out (February 2026):_
> _- 2026-02-28 | Thai Palace | -$38.50 | Dining Out [C]_
> _- 2026-02-22 | Chipotle | -$12.75 | Dining Out [C]_
> _..._
> _Total: -$342.17_

> **You:** Update that Shell Gas transaction -- it should be $44.50, not $42.
>
> **Claude** calls `manage_transactions` with action `update`:
>
> _Transaction updated:_
> _- 2026-03-04 | Shell Gas | -$44.50 | Transportation [U]_

## Available Actions

| Action         | Description                                                   |
| -------------- | ------------------------------------------------------------- |
| `list`         | List transactions with optional date/category filters         |
| `get`          | Get full details for a specific transaction                   |
| `create`       | Create a new transaction                                      |
| `update`       | Update an existing transaction's details                      |
| `delete`       | Delete a transaction                                          |
| `batch_create` | Create multiple transactions at once                          |
| `batch_update` | Update multiple transactions at once                          |
| `import`       | Import transactions (matches against existing by amount/date) |

---

## API Reference

<!-- prettier-ignore -->
::: ynab_mcp.tools.transactions.manage_transactions
    options:
      show_root_heading: true
      show_source: true
