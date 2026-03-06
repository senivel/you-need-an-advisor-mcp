# YNAB Terminology and Key Concepts

This resource explains foundational YNAB concepts and terminology. Understanding these terms is essential for interpreting budget data and giving accurate budgeting guidance.

## The Four Rules

YNAB's methodology is built on four rules:

1. **Give Every Dollar a Job** -- Every dollar of income must be assigned to a category before spending. When income arrives, it goes to "To Be Budgeted" (TBB) and must be allocated to categories. No money should sit unassigned.

2. **Embrace Your True Expenses** -- Break large, infrequent expenses into monthly amounts. If car insurance costs $1,200/year, budget $100/month. This prevents "surprise" expenses from derailing the budget. Use goals (see `ynab://knowledge/goals`) to automate this.

3. **Roll With the Punches** -- When overspending happens, move money between categories rather than abandoning the budget. YNAB is designed to be adjusted, not followed rigidly. Overspending in one category means reducing another.

4. **Age Your Money** -- Spend money that is at least 30 days old. When the gap between earning and spending grows, you break the paycheck-to-paycheck cycle. The Age of Money metric tracks this.

## Milliunits

The YNAB API represents all monetary amounts in **milliunits**, where **1,000 milliunits = $1.00** (or one unit of any currency). This avoids floating-point precision errors common with decimal currency math.

- **$50.00** = `50000` milliunits
- **$1,234.56** = `1234560` milliunits
- **-$20.00** = `-20000` milliunits (negative values represent outflows or debt)

To convert: divide milliunits by 1,000 for display, multiply display amounts by 1,000 for API calls. All API fields representing money (`balance`, `budgeted`, `activity`, `goal_target`, etc.) use milliunits.

## To Be Budgeted (TBB)

TBB represents money that has been received but not yet assigned to any category. It appears at the top of the budget view.

- **TBB should be zero** -- following Rule 1, all available money should be assigned to categories
- **Positive TBB** means unassigned money is available to budget
- **Negative TBB** means more money has been assigned to categories than is actually available -- this is overbudgeting and needs immediate correction by reducing category assignments

The API does not expose TBB as a single field. It is calculated from the budget month summary data.

## On-Budget vs Off-Budget Accounts

YNAB accounts fall into two categories, indicated by the `on_budget` API field:

**On-Budget accounts** (`on_budget: true`):

- Checking, savings, credit cards, cash, lines of credit
- Transactions in these accounts affect category balances
- Every transaction must be categorized
- These accounts participate in the budgeting workflow

**Off-Budget accounts** (`on_budget: false`):

- Tracking accounts for assets and liabilities (investments, mortgages, car loans)
- Transactions are tracked but do not affect category balances
- Useful for net worth tracking without budgeting complexity
- Transfers between on-budget and off-budget accounts are categorized (they represent money entering or leaving the budget)

## Age of Money

Age of Money measures the average age (in days) of the dollars you spend. It answers: "How long did this money sit in my accounts before I spent it?"

- **Target: 30+ days** -- spending money that is at least a month old means you are ahead of the paycheck cycle
- Calculated from the last 10 cash (non-credit) outflow transactions
- Only considers on-budget account outflows
- Available in the API via the budget month or budget settings data

A rising Age of Money indicates improving financial stability. A falling age suggests spending is outpacing income.

## Transaction States

Every transaction has a `cleared` field with one of three values:

- **`uncleared`** -- Transaction entered but not yet verified against bank records. Appears as gray in YNAB. New transactions start here.
- **`cleared`** -- Transaction confirmed to match a bank record. Marked by the user (or auto-import) with a green checkmark. The user has verified this transaction is real.
- **`reconciled`** -- Transaction locked during reconciliation. Appears with a padlock icon. Cannot be edited without first unreconciling. See `ynab://knowledge/reconciliation` for the reconciliation process.

The progression is: `uncleared` -> `cleared` -> `reconciled`. Transactions should be cleared regularly and reconciled periodically to ensure YNAB balances match actual bank balances.

## Key API Field Patterns

- **`deleted` field** -- Most API objects include a `deleted: true/false` field. Deleted items are soft-deleted and returned by the API but should be filtered out for display.
- **`transfer_account_id`** -- On payees, indicates this is a transfer payee linked to an account. On transactions, indicates a transfer transaction.
- **`flag_color`** -- User-assigned flags on transactions: `"red"`, `"orange"`, `"yellow"`, `"green"`, `"blue"`, `"purple"`, or `null`.
