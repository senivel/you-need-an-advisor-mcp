# Resources

MCP resources provide embedded YNAB methodology knowledge that the AI references automatically. Think of resources as the reference library your AI budgeting advisor has on its shelf -- it reads these to give you informed, accurate guidance rather than generic advice.

Resources are different from tools:

- **Resources** = Reference material the AI reads for context (like opening a guidebook)
- **Tools** = Actions the AI takes on your behalf (like making a transaction)

---

## Knowledge Resources

Static methodology resources that explain YNAB concepts and best practices. These are always available regardless of which budget you're using.

| URI                               | Name           | Description                                                                                                                                                      |
| --------------------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ynab://knowledge/terminology`    | Terminology    | YNAB terminology and key concepts: milliunits, on-budget vs off-budget accounts, Age of Money, TBB, the Four Rules, and transaction states.                      |
| `ynab://knowledge/credit-cards`   | Credit Cards   | Credit card handling in YNAB: the Credit Card Payment category, budgeting for purchases on credit, making payments, returns, pre-YNAB debt, and common mistakes. |
| `ynab://knowledge/goals`          | Goals          | YNAB goal types: Target Category Balance, Monthly Savings Builder, and Needed for Spending, with API field mappings and use case guidance.                       |
| `ynab://knowledge/overspending`   | Overspending   | Overspending behavior in YNAB: cash vs credit overspending, negative balance rollover, and strategies for handling overspent categories.                         |
| `ynab://knowledge/reconciliation` | Reconciliation | The reconciliation process: step-by-step instructions, transaction statuses, adjustment transactions, and best practices for regular reconciliation.             |

The AI reads these resources automatically when a prompt or conversation topic requires methodology knowledge. For example, when running the debt payoff planner, the AI reads the credit cards and overspending resources to provide accurate guidance.

---

## Budget Resources

Dynamic resources populated from your live YNAB data. These are per-budget and require a budget ID in the URI.

| URI Pattern                             | Name       | Description                                                                                                                                    |
| --------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `ynab://budgets/{budget_id}/accounts`   | Accounts   | All active (non-deleted) accounts with current balances, types, and on-budget status. Returns JSON.                                            |
| `ynab://budgets/{budget_id}/categories` | Categories | All visible category groups and categories with budgeted amounts, activity, and balances. Hidden and deleted items are excluded. Returns JSON. |
| `ynab://budgets/{budget_id}/payees`     | Payees     | All non-transfer, non-deleted payees with IDs and names. Transfer payees (linked to accounts) are excluded. Returns JSON.                      |

Budget resources give the AI immediate context about your budget structure. Instead of making multiple tool calls to understand your accounts, categories, and payees, the AI reads these resources upfront -- similar to glancing at your budget overview before diving into specifics.

!!! info "When are budget resources used?"
Budget resources are read at the start of most prompt workflows. For example, the `enter_transactions` prompt reads accounts and categories first so it can suggest the right ones for each transaction you enter.
