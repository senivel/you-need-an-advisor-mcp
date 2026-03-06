# Reconciliation in YNAB

Reconciliation is the process of confirming that YNAB's records match your bank's actual account balance. It is the primary way to ensure your budget reflects reality -- catching missing transactions, incorrect amounts, and duplicates before they compound into larger discrepancies.

## Why Reconciliation Matters

Without regular reconciliation, small errors accumulate. A $5 transaction entered as $50, a forgotten ATM withdrawal, or a duplicate import can throw off category balances and lead to incorrect budgeting decisions. Reconciliation catches these issues early and locks verified transactions so they cannot be accidentally modified.

## Transaction Statuses

Every transaction in YNAB has a `cleared` field with one of three values, representing its verification state:

### Uncleared (`"uncleared"`)

- Transaction has been entered in YNAB but **not yet confirmed** against bank records
- Appears with a gray indicator in YNAB
- New manually-entered transactions start in this state
- These transactions are included in the working balance but not the cleared balance
- May represent pending charges, scheduled transactions, or transactions not yet posted at the bank

### Cleared (`"cleared"`)

- Transaction has been **confirmed to match** a record at the bank
- Marked by the user clicking the cleared indicator (or automatically via bank import)
- Appears with a green checkmark in YNAB
- Included in the **cleared balance**, which is the balance used during reconciliation
- Clearing means: "I have verified this transaction is real and the amount is correct"

### Reconciled (`"reconciled"`)

- Transaction has been **locked during a reconciliation** event
- Appears with a padlock icon in YNAB
- **Cannot be edited** without first un-reconciling (which requires deliberate action)
- Represents the highest confidence level -- this transaction has been verified against a bank statement and the overall balance confirmed
- Reconciled transactions form the bedrock of trust in your budget data

The progression is: `uncleared` -> `cleared` -> `reconciled`. Each step increases confidence that YNAB matches reality.

## Step-by-Step Reconciliation Process

### Step 1: Get Your Bank Balance

Log in to your bank's website or mobile app (or use a paper statement) and note the **current posted balance** for the account. This is the balance excluding pending transactions -- only fully posted items.

### Step 2: Clear All Matching Transactions

In YNAB, review uncleared transactions for this account. For each transaction that appears on your bank statement or online banking:

- Verify the amount matches
- Verify the date is reasonable (bank posting dates may differ slightly from transaction dates)
- Click to mark it as **cleared**

Any transactions in YNAB that do NOT appear at the bank should remain uncleared (they may be pending or entered in advance).

### Step 3: Compare Balances

YNAB displays a **cleared balance** for each account -- this is the sum of all cleared and reconciled transactions. Compare this cleared balance to the bank balance you recorded in Step 1.

### Step 4a: Balances Match

If YNAB's cleared balance equals the bank balance:

- Click **Reconcile** in YNAB
- All cleared transactions become **reconciled** (locked)
- The reconciliation point is saved -- future reconciliations only need to verify transactions since this point
- You are done

### Step 4b: Balances Do Not Match

If the balances differ, there is a discrepancy. Common causes:

- A transaction in YNAB has the wrong amount
- A transaction at the bank is missing from YNAB
- A duplicate transaction exists in YNAB (often from both manual entry and bank import)
- A transaction was cleared in YNAB but has not actually posted at the bank

Work through the transactions to find and fix the discrepancy, then try reconciling again.

### Step 5: Adjustment Transactions (Last Resort)

If you cannot find the discrepancy after thorough review, YNAB offers to create an **adjustment transaction**. This is a special transaction that forces the cleared balance to match the bank balance.

- The adjustment is categorized to a category you choose (often "To Be Budgeted" or an "Adjustments" category)
- It represents money that is unaccounted for -- either a missed transaction or an error that could not be traced
- **Use this sparingly.** Frequent adjustments indicate a problem with transaction entry habits
- The adjustment amount reveals the size of the discrepancy, which can help identify the root cause later

## When to Reconcile

Reconciliation frequency depends on account activity:

| Account Type     | Recommended Frequency | Why                                                             |
| ---------------- | --------------------- | --------------------------------------------------------------- |
| Active checking  | Weekly or more        | High transaction volume; errors compound quickly                |
| Credit cards     | Weekly                | Catches missed purchases and verifies statement accuracy        |
| Savings accounts | Monthly               | Low transaction volume; fewer opportunities for error           |
| Cash accounts    | As needed             | No bank to reconcile against; verify physical cash periodically |

The more frequently you reconcile, the fewer transactions you need to review each time. Daily reconciliation for active accounts takes only a minute or two and keeps the budget accurate.

## Common Reconciliation Issues

**Pending transactions at the bank not yet in YNAB:**
If your bank shows a pending charge that you have not entered in YNAB, do not include it in reconciliation. Enter it as an uncleared transaction -- it will be cleared and reconciled in a future session once it posts.

**Transactions entered with the wrong amount:**
A common source of discrepancy. The fix is to correct the amount in YNAB to match the bank. This may affect category balances -- verify the category is still correctly funded after the correction.

**Duplicate transactions from import and manual entry:**
When you enter a transaction manually and the bank also imports it, you may end up with two copies. YNAB attempts auto-matching, but it can miss if amounts or dates differ slightly. Delete the duplicate and keep the correctly categorized version.

**Timing differences between bank posting and transaction dates:**
A purchase made on Friday may not post until Monday. If you entered it in YNAB on Friday but the bank shows it on Monday, the dates will differ. This is normal -- clear the transaction in YNAB when you see it posted at the bank, regardless of the date difference.

**Interest and fees not entered:**
Banks may add interest, maintenance fees, or other charges that you did not manually enter. Check your bank transactions for any items not in YNAB and add them with appropriate categories.

## API Field Mappings

When working with YNAB API data for reconciliation-related features:

- **`cleared` field on transactions**: Values are `"cleared"`, `"uncleared"`, or `"reconciled"` -- represents the verification state
- **`cleared_balance` on accounts**: The sum of all cleared and reconciled transactions; this is the balance compared against the bank during reconciliation
- **`uncleared_balance` on accounts**: The sum of all uncleared transactions; represents pending or unverified activity
- **`balance` on accounts**: The total balance (cleared + uncleared); represents the expected balance once all transactions post
- **`last_reconciled_at` on accounts**: Timestamp of the most recent reconciliation (if available)
- To filter transactions by status, use the `cleared` field: transactions with `"reconciled"` have been verified; `"cleared"` are confirmed but not yet locked; `"uncleared"` need attention

## Cross-References

- `ynab://knowledge/terminology` -- Transaction state definitions, account types, and key API field patterns
