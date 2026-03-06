# Analysis Prompts

These prompts help you understand your budget's current state and trends. Each one guides the AI through a structured analysis workflow -- fetching your data, interpreting it, and delivering clear, actionable insights.

Analysis prompts are what make YNAB MCP more than an API wrapper. Instead of raw numbers, you get a budgeting advisor that knows what to look for.

!!! tip "Budget ID is optional"
All analysis prompts accept an optional `budget_id` parameter. If you don't provide one, the AI will look up your budgets first and ask which one to use.

---

## Budget Health Analysis

**What it does:** A comprehensive assessment of your budget's overall health, covering your To Be Budgeted balance, overspending (distinguishing cash vs credit), underfunded goals, and improvement recommendations.

**When to use:**

- Monthly budget check-in
- After a large unexpected expense
- When you feel like your budget is "off" but can't pinpoint why
- Before making a major financial decision

**Parameters:**

| Parameter   | Required | Description                                               |
| ----------- | -------- | --------------------------------------------------------- |
| `budget_id` | No       | The budget to analyze. Resolved automatically if omitted. |

**What you'll get:** A structured report covering your TBB state, any overspent categories (with cash vs credit distinction), underfunded goals, and prioritized recommendations for getting back on track.

---

## Spending Trends

**What it does:** Multi-month spending comparison that identifies categories with increasing, decreasing, or volatile spending patterns over the last 3 months.

**When to use:**

- Wondering where your money has been going lately
- Preparing for a budget adjustment
- Identifying lifestyle creep
- Quarterly financial review

**Parameters:**

| Parameter   | Required | Description                                               |
| ----------- | -------- | --------------------------------------------------------- |
| `budget_id` | No       | The budget to analyze. Resolved automatically if omitted. |

**What you'll get:** Month-over-month spending changes by category, categories with the largest increases, and trend lines that highlight where your spending habits are shifting.

---

## Budget Setup Advisor

**What it does:** First-time YNAB budget setup guidance that walks through creating accounts, organizing categories, performing initial allocation, and explaining the Four Rules in practical terms.

**When to use:**

- Setting up YNAB for the first time
- Starting fresh with a new budget
- Helping a partner or family member get started
- Restructuring an existing budget from scratch

**Parameters:**

| Parameter   | Required | Description                                              |
| ----------- | -------- | -------------------------------------------------------- |
| `budget_id` | No       | The budget to set up. Resolved automatically if omitted. |

**What you'll get:** A step-by-step walkthrough from account creation through initial budget allocation, with coaching-style explanations of why each step matters.

---

## Debt Payoff Planner

**What it does:** Identifies all debt accounts and presents avalanche and snowball payoff strategies with trade-offs, helping you choose and implement a plan.

**When to use:**

- Ready to tackle debt systematically
- Comparing payoff strategies (avalanche vs snowball)
- Reviewing progress on an existing payoff plan
- After paying off a debt and reallocating payments

**Parameters:**

| Parameter   | Required | Description                                               |
| ----------- | -------- | --------------------------------------------------------- |
| `budget_id` | No       | The budget to analyze. Resolved automatically if omitted. |

**What you'll get:** A debt inventory with balances and rates, side-by-side comparison of payoff strategies, estimated payoff timelines, and a recommended action plan.

---

## Savings Goal Tracker

**What it does:** Lists all savings goals, calculates progress percentages, identifies underfunded goals, and creates prioritized funding recommendations.

**When to use:**

- Checking progress toward savings targets
- Deciding which goal to fund next
- After receiving extra income
- Monthly goal review

**Parameters:**

| Parameter   | Required | Description                                               |
| ----------- | -------- | --------------------------------------------------------- |
| `budget_id` | No       | The budget to analyze. Resolved automatically if omitted. |

**What you'll get:** A progress dashboard for all goals showing funded vs target amounts, percentage complete, and a prioritized list of which goals need attention most.

---

## Income Allocation

**What it does:** Guides through allocating new income following YNAB's recommended priority order: immediate obligations, true expenses, quality of life, and savings goals.

**When to use:**

- Payday -- allocating new income
- Received a bonus or windfall
- Learning the YNAB allocation philosophy
- Redistributing funds after a category adjustment

**Parameters:**

| Parameter   | Required | Description                                               |
| ----------- | -------- | --------------------------------------------------------- |
| `budget_id` | No       | The budget to analyze. Resolved automatically if omitted. |

**What you'll get:** A guided allocation workflow that walks through each priority tier, showing where your money should go first and why, based on your actual budget categories and goals.

---

## Example Conversation

Here's what using the `budget_health_analysis` prompt looks like in practice:

```
User: Use the budget_health_analysis prompt

AI: I'll run a comprehensive health check on your budget. Let me start
    by finding your budget...

    [Calls manage_budgets with action="list"]
    [Calls manage_months to get current month data]
    [Reads budget categories and accounts]

    ## Budget Health Report

    **To Be Budgeted:** $142.50
    Your TBB is positive -- good, no overassignment.

    **Overspending:** 1 category
    - Dining Out: -$45.00 (cash overspending -- this will deduct from
      next month's TBB)

    **Underfunded Goals:** 3 categories
    - Emergency Fund: $200 short of monthly target
    - Car Insurance: $75 short of savings builder target
    - Vacation: $150 short of target balance goal

    **Recommendations:**
    1. Cover the Dining Out overspending first ($45)
    2. Fund Emergency Fund next -- it's your safety net
    3. Remaining $97.50 toward Car Insurance (due sooner)
```
