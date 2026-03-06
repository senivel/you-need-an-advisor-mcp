# Workflow Guides

Step-by-step guides for common YNAB workflows and life situations. These prompts go beyond data analysis -- they walk you through complete processes, from understanding the concept to taking action in your budget.

Each workflow guide reads relevant YNAB methodology resources and references specific tools, so the AI acts as an informed budgeting coach rather than a generic assistant.

!!! tip "Budget ID is optional"
All workflow guides accept an optional `budget_id` parameter. If you don't provide one, the AI will look up your budgets first and ask which one to use.

---

## Getting Started with YNAB

**What it does:** Walks a new user through creating their first YNAB budget, from account setup through category creation and initial allocation.

**When to use:**

- Brand new to YNAB
- Setting up a budget for the first time
- Helping someone else get started with YNAB
- Want a guided tour of the YNAB approach

**Parameters:**

| Parameter   | Required | Description                                              |
| ----------- | -------- | -------------------------------------------------------- |
| `budget_id` | No       | The budget to set up. Resolved automatically if omitted. |

**What you'll get:** A supportive walkthrough covering account creation, category organization, your first allocation following the Four Rules, and what to do next.

---

## Getting Out of Debt

**What it does:** Guides you through building a complete debt payoff plan, covering debt inventory, strategy selection, and implementation in YNAB.

**When to use:**

- Serious about eliminating debt
- Want to understand avalanche vs snowball approaches
- Setting up debt categories and payment workflows
- Need motivation and a concrete plan

**Parameters:**

| Parameter   | Required | Description                                                 |
| ----------- | -------- | ----------------------------------------------------------- |
| `budget_id` | No       | The budget to configure. Resolved automatically if omitted. |

**What you'll get:** A debt inventory, strategy comparison (avalanche vs snowball with your actual numbers), category setup instructions, and a systematic payment workflow.

---

## Irregular Income

**What it does:** Guides freelancers, commission earners, and anyone with variable income through income smoothing, the buffer concept, and monthly workflow adjustments.

**When to use:**

- Freelancer or self-employed
- Commission-based income
- Seasonal work with income fluctuations
- Any situation where paychecks vary significantly

**Parameters:**

| Parameter   | Required | Description                                                 |
| ----------- | -------- | ----------------------------------------------------------- |
| `budget_id` | No       | The budget to configure. Resolved automatically if omitted. |

**What you'll get:** An explanation of the income buffer concept, a workflow for handling variable paychecks, strategies for feast/famine cycles, and category setup recommendations.

---

## Couples Budgeting

**What it does:** Guides couples through setting up shared finances in YNAB, covering budget structure options, account setup for partners, and the budget meeting workflow.

**When to use:**

- Combining finances with a partner
- Setting up a shared YNAB budget
- Establishing fun money categories
- Creating a regular budget meeting routine

**Parameters:**

| Parameter   | Required | Description                                                 |
| ----------- | -------- | ----------------------------------------------------------- |
| `budget_id` | No       | The budget to configure. Resolved automatically if omitted. |

**What you'll get:** Budget structure recommendations for couples, account setup for shared and individual spending, fun money category setup, and a budget meeting template.

---

## Emergency Fund

**What it does:** Guides you through building an emergency fund, from calculating your target amount to setting up the right goal type and funding strategy.

**When to use:**

- Starting to build an emergency fund
- Reassessing your emergency fund target
- Setting up the right YNAB goal type for your fund
- Deciding when to use vs replenish your fund

**Parameters:**

| Parameter   | Required | Description                                                 |
| ----------- | -------- | ----------------------------------------------------------- |
| `budget_id` | No       | The budget to configure. Resolved automatically if omitted. |

**What you'll get:** A target calculation based on your expenses, goal type recommendation, funding strategy, and guidelines for when to use your emergency fund.

---

## Breaking Paycheck to Paycheck

**What it does:** Guides you through the process of aging your money past 30 days, building a buffer, and breaking the paycheck-to-paycheck cycle.

**When to use:**

- Living paycheck to paycheck
- Want to understand Age of Money
- Ready to build a one-month buffer
- Need a milestone-based plan for financial stability

**Parameters:**

| Parameter   | Required | Description                                               |
| ----------- | -------- | --------------------------------------------------------- |
| `budget_id` | No       | The budget to analyze. Resolved automatically if omitted. |

**What you'll get:** An explanation of Age of Money, a buffer building strategy with milestones, practical tips for accelerating progress, and long-term maintenance guidance.

---

## Example Conversation

Here's what using the `getting_out_of_debt` workflow guide looks like in practice:

```
User: Use the getting_out_of_debt prompt

AI: Let's build a debt payoff plan together. First, let me look at
    your budget...

    [Calls manage_budgets with action="list"]
    [Reads ynab://knowledge/credit-cards for methodology context]
    [Calls manage_budgets with action="get" to see accounts]

    ## Your Debt Inventory

    | Account          | Balance    | Type        |
    | ---------------- | ---------- | ----------- |
    | Visa Card        | $3,200     | Credit Card |
    | Student Loan     | $18,500    | Loan        |
    | Car Loan         | $8,400     | Loan        |

    ## Strategy Comparison

    **Avalanche (highest interest first):**
    Saves $1,240 in interest, payoff in 28 months

    **Snowball (smallest balance first):**
    Costs $1,240 more, but first win in 6 months (Visa paid off)

    Which approach feels right for you? The avalanche saves money,
    but the snowball gives you quick wins for motivation.
```
