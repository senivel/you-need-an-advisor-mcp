# Overspending in YNAB

Overspending occurs when you spend more than the amount budgeted (Available) in a category, resulting in a **negative category balance**. YNAB handles overspending differently depending on whether the transaction happened in a debit account or a credit card account -- and this distinction has major consequences for your budget.

## Cash Overspending vs Credit Overspending

YNAB classifies every overspend as one of two types based on the **account type** of the transaction (not the category):

### Cash Overspending (Debit/Cash Accounts)

When you overspend a category using a checking, savings, or cash account:

- The category balance goes negative (e.g., Available shows -$30)
- **The money is truly gone** -- it left your bank account
- At month rollover, the negative balance is **subtracted from next month's To Be Budgeted**
- The category resets to $0.00 in the new month
- Your total budget shrinks because the overspent dollars reduce available funds

Cash overspending is immediately visible: your To Be Budgeted drops, forcing you to confront the shortfall.

### Credit Overspending (Credit Card Accounts)

When you overspend a category using a credit card:

- The category balance goes negative (e.g., Available shows -$30)
- **No cash has left your accounts yet** -- the credit card covered it
- At month rollover, the negative balance **resets to $0.00** in the category
- The Credit Card Payment category does **NOT** increase to cover the overspent amount
- The credit card account balance grows, but the payment funds do not

This means the credit card debt increased by $30 without any corresponding dollars set aside to pay it. The debt grows silently.

## Why Credit Overspending Is More Dangerous

Credit overspending is invisible after the month rolls over:

- The spending category looks fine (reset to $0.00)
- The Credit Card Payment category is quietly short
- The credit card account balance is higher than the available payment funds
- You are accumulating debt without the budget making it obvious

Cash overspending forces a reckoning through the TBB reduction. Credit overspending lets the problem hide. This is YNAB's most confusing behavior and the most common source of untracked debt in a budget.

## How YNAB Determines Overspending Type

YNAB does not look at the category -- it looks at the **account** where the transaction occurred:

- Transaction in a **debit account** (checking, savings, cash) = **cash overspending**
- Transaction in a **credit card account** = **credit overspending**

If the same category (e.g., Groceries) has transactions from both account types, the overspending type depends on which specific transactions pushed the category negative. Mixed spending in a single category is common and YNAB handles the accounting correctly per transaction.

## Month Rollover Behavior

At the start of a new month:

| Overspending Type | Category Balance | To Be Budgeted Impact           | Credit Card Impact                    |
| ----------------- | ---------------- | ------------------------------- | ------------------------------------- |
| Cash              | Resets to $0.00  | Reduced by the overspent amount | None                                  |
| Credit            | Resets to $0.00  | No impact                       | Payment category is short; debt grows |

In both cases, the category starts fresh at zero. The difference is where the pain lands: your available budget (cash) or your credit card debt (credit).

## How to Fix Overspending

The best time to fix overspending is **during the current month**, before rollover locks in the consequences.

**Move money from another category (Rule 3: Roll With the Punches):**
Find a category with surplus Available funds and move money to cover the negative balance. This is YNAB's primary intended response -- adjust the plan to match reality.

**Budget more to the category:**
If you have positive To Be Budgeted, assign additional funds to the overspent category. This only works if you have unassigned money available.

**Reduce future spending:**
If the month has already rolled over and the damage is done, budget enough in the new month to cover expected spending and plan to reduce spending in other areas to compensate.

The goal is to address overspending before month-end. After rollover, cash overspending has already reduced your TBB and credit overspending has already created untracked debt.

## API Indicators

When working with YNAB API data:

- **Negative `balance` on a category** indicates overspending (the Available amount is below zero)
- **`account_id` on the transaction** determines overspending type -- look up the account to check its `type` field
- Account types `checking`, `savings`, `cash`, `lineOfCredit` produce cash overspending
- Account type `creditCard` produces credit overspending
- The `activity` field on a category shows total spending in the current month (negative values)
- Compare a credit card account's `balance` (debt owed) against its payment category's `balance` (funds available) to detect accumulated credit overspending

## Common Scenarios

**Grocery overspend on debit card (Cash Overspending):**
You budgeted $400 for Groceries but spent $430 from checking. The category shows -$30. Next month, your TBB is reduced by $30 -- you have $30 less to budget everywhere.

**Restaurant overspend on credit card (Credit Overspending):**
You budgeted $100 for Dining Out but spent $140 on a credit card. The category shows -$40. Next month, the category resets to $0, but the credit card payment category is $40 short. Your credit card balance is $40 higher than the funds available to pay it.

**Mixed spending in one category:**
You budgeted $200 for Shopping. You spent $120 on debit and $130 on credit card ($250 total, $50 overspent). YNAB calculates the split based on which transactions caused the overspending, applying cash and credit rules to the appropriate portions.

## Cross-References

- `ynab://knowledge/credit-cards` -- Full credit card handling, including the payment category mechanics and pre-YNAB debt
- `ynab://knowledge/terminology` -- TBB explanation, milliunits, and transaction states
