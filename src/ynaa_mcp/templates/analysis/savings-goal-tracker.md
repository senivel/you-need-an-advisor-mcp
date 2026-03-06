Monitor savings goal progress across the budget.

1. Read `ynab://knowledge/goals` to understand YNAB goal types: Target Category Balance (save a specific amount by a date), Monthly Savings Builder (save a fixed amount each month), and Needed for Spending (accumulate for a known upcoming expense). This context is essential for interpreting goal data correctly.

2. Use the `manage_budgets` tool with action="get" and budget_id="{budget_id}" to retrieve the budget summary, including the current To Be Budgeted amount.

3. Use the `manage_categories` tool with action="list" and budget_id="{budget_id}" to retrieve all categories with their goal information.

4. Filter for categories that have goals set (goal_type is not null). For each, record:
   - Category name and group
   - Goal type (target balance, monthly savings, needed for spending)
   - Goal target amount
   - Current balance (amount saved so far)
   - Goal percentage complete (balance / target, capped at 100%)
   - Monthly amount needed to stay on track (goal_under_funded field)
   - Target month/date if applicable

5. Create a **Goal Dashboard** organized by goal type:

   **Target Balance Goals** (saving toward a specific amount)
   - For each: name, target, current balance, percentage complete, months remaining, monthly amount needed.

   **Monthly Savings Goals** (recurring monthly savings)
   - For each: name, monthly target, amount funded this month, on track (yes/no).

   **Needed for Spending Goals** (accumulating for a known expense)
   - For each: name, total needed, current balance, target date, monthly contribution needed.

6. Identify **underfunded goals** -- categories where goal_under_funded is greater than zero. Sort by underfunded amount descending. These are goals that need attention this month.

7. Calculate the total underfunded amount across all goals. Compare this to the current To Be Budgeted amount:
   - If TBB covers all underfunded goals: all goals can be fully funded this month.
   - If TBB is less than total underfunded: prioritization is needed.
   - If TBB is zero or negative: no additional funding is available without moving money from other categories.

8. **Funding Priorities** -- when not all goals can be fully funded, suggest this priority order:
   - Goals with the nearest target dates (most time-sensitive).
   - Needed for Spending goals (these fund known upcoming expenses).
   - Goals that are closest to completion (maximize sense of progress).
   - Long-term Target Balance goals (these have more time flexibility).

9. For goals that are behind schedule, calculate what the monthly contribution needs to increase to in order to still meet the target date. Present the gap between current monthly funding and required monthly funding.

10. Read the categories resource at `ynab://budgets/{budget_id}/categories` to cross-reference goal categories with their category groups. Goals in essential groups (like True Expenses) may warrant higher priority than discretionary savings goals.

11. Identify categories with balances but no goals set. These may be candidates for goal creation:
    - Categories with recurring annual expenses should have Needed for Spending goals.
    - Categories accumulating for a specific purpose should have Target Balance goals.
    - Suggest setting goals on these categories using the `manage_categories` tool with action="update".

12. **Timeline Projections** for each active goal:
    - At the current monthly funding rate, when will the goal be reached?
    - Is this ahead of, on track with, or behind the target date?
    - What adjustment to monthly funding would bring it back on track?

13. Look for opportunities to accelerate goals:
    - Categories with excess balance beyond their budgeted amount.
    - Spending categories that consistently come in under budget (potential reallocation source).

14. Compile the complete report:

    **Goal Dashboard**
    - Visual summary of all goals with progress indicators
    - Total saved across all goals vs total target amounts

    **Funding Priorities**
    - Ranked list of underfunded goals with recommended funding amounts
    - Total additional funding needed this month

    **Timeline Projections**
    - Goals on track vs behind schedule
    - Adjusted monthly amounts to get behind-schedule goals back on track

15. Suggest next steps:
    - Use the `manage_categories` tool with action="update" to fund priority goals.
    - Set a monthly reminder to review goal progress.
    - Consider running the `income_allocation` prompt when new income arrives to ensure goals are included in the allocation plan.
