Guide through allocating new income following YNAB priorities.

1. Use the `manage_budgets` tool with action="get" and budget_id="{budget_id}" to check the current To Be Budgeted (TBB) amount. This is the money available to assign to categories.

2. If TBB is zero or negative, there is no new income to allocate. Explain that income allocation applies when new money arrives (paycheck, refund, transfer in) and the TBB amount increases. If TBB is negative, the budget is over-assigned and needs adjustment before new allocation.

3. Use the `manage_categories` tool with action="list" and budget_id="{budget_id}" to retrieve all categories with their current budgeted amounts, balances, and goal status.

4. Read the categories resource at `ynab://budgets/{budget_id}/categories` to see the full category group structure.

5. Organize categories into YNAB's recommended priority groups. Allocate income in this order -- fund each level before moving to the next:

   **Priority 1: Immediate Obligations**
   These are non-negotiable expenses due before the next paycheck:
   - Rent or mortgage payment
   - Utilities (electric, gas, water, internet)
   - Groceries and essential food
   - Transportation (gas, transit passes, car payment)
   - Minimum debt payments (credit card minimums, loan minimums)
   - Insurance premiums due this period
   - Any other bills due before the next income arrives

6. For each Immediate Obligations category, check the current balance vs the amount needed. Use the `manage_categories` tool with action="update" and budget_id="{budget_id}" to assign funds. Only budget what is needed to cover obligations before the next paycheck, not the entire month if money is tight.

7. **Priority 2: True Expenses (Sinking Funds)**
   These are larger, non-monthly expenses broken into monthly contributions:
   - Car maintenance and repair fund
   - Home maintenance fund
   - Medical and dental expenses
   - Annual subscriptions and memberships
   - Holiday and gift fund
   - Clothing replacement
   - Pet care
     Check goal_under_funded for these categories to see how much is needed to stay on track.

8. Fund True Expenses categories. If there is not enough TBB to fully fund all sinking funds, prioritize:
   - Categories with upcoming due dates (time-sensitive).
   - Categories with the largest underfunding gap.
   - Categories where skipping a month creates a significant shortfall.

9. **Priority 3: Quality of Life**
   These are discretionary but important for well-being:
   - Dining out and restaurants
   - Entertainment (streaming, movies, events)
   - Hobbies and recreation
   - Personal care (haircuts, gym membership)
   - Subscriptions (non-essential)
     Fund these based on what brings value -- it is okay and healthy to budget for enjoyment.

10. **Priority 4: Savings Goals**
    After obligations, true expenses, and quality of life are covered:
    - Emergency fund contributions
    - Retirement savings beyond employer match
    - Vacation fund
    - Large purchase savings (furniture, electronics)
    - Investment contributions
      Check these categories' goals using the category data to determine target amounts.

11. After working through all four priority levels, use the `manage_budgets` tool with action="get" to verify the TBB amount:
    - **TBB is zero**: Every dollar has a job. The allocation is complete.
    - **TBB is positive**: There are still dollars to assign. Review if any priority categories were underfunded, or add to savings goals.
    - **TBB is negative**: Over-assigned. Pull back from the lowest-priority categories that were funded.

12. Handle the case where income does not cover all priorities:
    - This is normal, especially on a tight budget or when starting out.
    - Fund only through the priority level that the available money covers.
    - Do not fund Quality of Life or Savings if Immediate Obligations are not fully covered.
    - When the next paycheck arrives, continue where the allocation left off.

13. For categories with goals, compare the funded amount against the goal requirement:
    - Use the `manage_categories` tool with action="list" to check goal_under_funded after allocation.
    - If critical goals are still underfunded, note them for the next income allocation.

14. Present a summary of the allocation:

    **Allocation Summary**
    - Starting TBB: [amount before allocation]
    - Ending TBB: [amount after allocation, ideally zero]

    **By Priority Level**
    - Immediate Obligations: [total assigned] -- [fully funded / partially funded]
    - True Expenses: [total assigned] -- [fully funded / partially funded]
    - Quality of Life: [total assigned] -- [fully funded / partially funded]
    - Savings Goals: [total assigned] -- [fully funded / partially funded]

    **Still Needed**
    - Categories that could not be fully funded this cycle
    - Amount needed at next income to catch up

15. Remind the user of key principles:
    - Only budget money that is actually available right now (Rule 1).
    - It is okay to not fund everything in one paycheck -- assign more when the next income arrives.
    - If priorities shift mid-month, move money between categories freely (Rule 3: Roll With the Punches).
    - Over time, the goal is to be budgeting money that is at least 30 days old (Rule 4: Age Your Money).
