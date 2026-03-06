# Core Prompts

Essential everyday prompts for common YNAB tasks. These are the foundational prompts that ship with YNAB MCP -- the operations you'll use most frequently when interacting with your budget through an AI assistant.

Core prompts focus on the day-to-day: reviewing what you spent, entering new transactions, and checking your budget's pulse.

!!! tip "Budget ID is optional"
All core prompts accept an optional `budget_id` parameter. If you don't provide one, the AI will look up your budgets first and ask which one to use.

---

## Review Monthly Spending

**What it does:** Guides the AI through a complete review of a specific month's spending, reading budget context via MCP resources and then analyzing transactions and category activity.

**When to use:**

- End-of-month spending review
- Comparing spending to what you budgeted
- Looking for categories that went over or under
- Preparing for next month's budget adjustments

**Parameters:**

| Parameter   | Required | Description                                                |
| ----------- | -------- | ---------------------------------------------------------- |
| `month`     | Yes      | The month to review in `YYYY-MM` format (e.g., `2025-01`). |
| `budget_id` | No       | The budget to analyze. Resolved automatically if omitted.  |

**What you'll get:** A month-in-review report with spending by category, comparison to budgeted amounts, notable transactions, and observations about your spending patterns.

---

## Enter Transactions

**What it does:** Guides the AI through entering one or more transactions, reading account and category context first so it can suggest the right account and category for each transaction.

**When to use:**

- Recording purchases from the day
- Entering a batch of receipts
- Logging a payment or transfer
- Any time you need to add transactions to your budget

**Parameters:**

| Parameter   | Required | Description                                                           |
| ----------- | -------- | --------------------------------------------------------------------- |
| `budget_id` | No       | The budget to add transactions to. Resolved automatically if omitted. |

**What you'll get:** A guided transaction entry workflow where the AI reads your accounts and categories first, then helps you enter each transaction with the correct account, payee, category, and amount.

---

## Budget Health Check

**What it does:** Guides the AI through a quick budget health review, reading account and category data to assess overall budget health.

**When to use:**

- Quick daily or weekly check-in
- Want a snapshot of budget status without deep analysis
- Checking if anything needs immediate attention
- Verifying the budget looks right after changes

**Parameters:**

| Parameter   | Required | Description                                             |
| ----------- | -------- | ------------------------------------------------------- |
| `budget_id` | No       | The budget to check. Resolved automatically if omitted. |

**What you'll get:** A quick-look health summary covering your TBB balance, any overspent categories, and whether your budget needs attention.

!!! note "Health Check vs Health Analysis"
The core `budget_health_check` prompt provides a quick snapshot. For a deeper analysis with recommendations, use the [Budget Health Analysis](analysis-prompts.md#budget-health-analysis) prompt from the Analysis Prompts section.

---

## Example Conversation

Here's what using the `review_monthly_spending` prompt looks like:

```
User: Use the review_monthly_spending prompt for 2025-01

AI: Let me review your January spending. First, I'll pull up your
    budget context...

    [Reads ynab://budgets/{id}/categories for category structure]
    [Reads ynab://budgets/{id}/accounts for account context]
    [Calls manage_months to get January data]
    [Calls manage_transactions to get January transactions]

    ## January 2025 Spending Review

    **Total Spent:** $4,230
    **Total Budgeted:** $4,500
    **Under Budget By:** $270

    **Top Categories:**
    - Housing: $1,800 (on budget)
    - Groceries: $620 ($70 over budget)
    - Dining Out: $285 ($35 over budget)
    - Transportation: $340 (on budget)

    **Notable:** Groceries and Dining Out were both over budget.
    Together that's $105 of overspending. Your other categories
    came in under, which absorbed the difference. Consider
    adjusting those targets for February.
```
