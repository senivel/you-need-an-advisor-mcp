Perform a comprehensive budget health analysis.

1. Use the `manage_budgets` tool with action="get" and budget_id="{budget_id}" to retrieve the budget summary, including the To Be Budgeted (TBB) amount.

2. Evaluate the TBB state and explain what it means for the user's budget:
   - **Positive TBB**: Money is available but not yet assigned to categories. Per Rule 1 (Give Every Dollar a Job), guide the user to assign these dollars.
   - **Zero TBB**: Ideal state -- every dollar has a job. Confirm the budget is fully allocated.
   - **Negative TBB**: The user has over-assigned money. This is urgent -- categories promise more than the budget has. Identify where to pull back.

3. Read the accounts resource at `ynab://budgets/{budget_id}/accounts` to see all account balances.

4. Summarize account health:
   - Total across all on-budget accounts (checking + savings).
   - Note any accounts with negative balances.
   - Flag credit card accounts and their current balances (amounts owed).

5. Read the categories resource at `ynab://budgets/{budget_id}/categories` to see all category groups and their budgeted/activity/balance amounts.

6. Use the `manage_categories` tool with action="list" and budget_id="{budget_id}" to get full category detail including goal status.

7. Scan for overspent categories (negative balance). For each overspent category, note:
   - Category name and overspent amount.
   - Whether it is **cash overspending** or **credit overspending**.
   - Cash overspending is more urgent: it steals directly from next month's To Be Budgeted amount.
   - Credit overspending creates debt on the credit card but does not reduce next month's TBB.

8. If any overspending is found, read `ynab://knowledge/overspending` to understand the mechanics and provide accurate guidance on resolving it.

9. Identify categories with goals that are underfunded:
   - Use the goal_under_funded field from category data.
   - List the top 5 most underfunded categories by dollar amount.
   - Note the goal type (target balance, monthly savings, needed for spending) for context.

10. Check for categories with zero budgeted but positive activity (spending without a budget allocation). These indicate unplanned spending.

11. Use the `manage_budgets` tool with action="get" to check Age of Money if available. Explain what it indicates:
    - Under 30 days: living paycheck to paycheck.
    - 30-60 days: building a buffer.
    - Over 60 days: strong financial cushion.

12. Calculate the ratio of total budgeted to total spending across all categories. A ratio well above 1.0 suggests conservative budgeting; below 1.0 suggests systemic overspending.

13. Look at category groups as a whole. Identify if any entire group is consistently overspent or significantly underfunded.

14. Compile findings into a structured report:

    **Budget Health Summary**
    - TBB status and interpretation
    - Total account balances
    - Age of Money assessment

    **Key Concerns**
    - Overspent categories (prioritize cash overspending)
    - Underfunded goals
    - Unplanned spending categories

    **Action Items**
    - Specific, prioritized steps to improve budget health
    - Which categories to cover first
    - Whether to adjust goals or reallocate funds

15. Cross-reference: If significant category-level issues are found, suggest running the `spending_trends` prompt for a deeper multi-month analysis of problem categories.
