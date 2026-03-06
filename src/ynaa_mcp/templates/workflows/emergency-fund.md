Building an emergency fund is one of the most important things you can do for your financial security. This guide will help you calculate your target, set it up in YNAB, and fund it strategically.

1. Read the knowledge resource at `ynab://knowledge/goals` to understand YNAB's goal types. We'll use a Target Balance goal for your emergency fund -- it's designed for exactly this purpose.

2. First, let's figure out how much you need. A solid emergency fund covers **3 to 6 months of essential expenses**. Not 3-6 months of income -- just the expenses you'd need to survive if your income stopped: housing, food, utilities, insurance, transportation, and minimum debt payments.

3. Use `manage_months` with action="get" to pull up a recent typical month. Look at your spending in essential categories to estimate your monthly baseline. Multiply that by your target number of months (3 months if you have stable income, 6 months if your income is variable or you're the sole earner).

4. Read the categories resource at `ynab://budgets/{budget_id}/categories` to see your current category structure. We'll add the emergency fund here.

5. Use `manage_categories` with action="create_category" to create an "Emergency Fund" category. Place it in a savings-oriented group, or create a new group called "Financial Security" using `manage_categories` with action="create_group" first.

6. Now set a goal on your emergency fund category. Use `manage_categories` with action="update" to set a Target Balance goal with the amount you calculated in step 3. YNAB will show you how much you need to save each month to reach your target.

7. Where does the emergency fund fit in your priority order? Here's a good framework:
   - **First**: Immediate obligations (rent, food, utilities, minimum debt payments)
   - **Second**: A starter emergency fund of $1,000 (or one month's expenses)
   - **Third**: Debt payoff (especially high-interest debt)
   - **Fourth**: Full emergency fund (3-6 months)
   - **Fifth**: Other savings goals

8. Don't try to fund it all at once. Use `manage_categories` with action="update" to assign whatever you can each month. Even $50/month builds to $600/year. The important thing is consistency.

9. Look for money to accelerate your emergency fund. Common sources:
   - Windfalls (tax refunds, bonuses, gifts)
   - Spending reductions in flexible categories
   - Selling things you no longer need
   - Any amount left in categories at month's end that can be redirected

10. Track your progress. Use `manage_categories` with action="get" to check your emergency fund balance and goal progress. Watching the percentage climb is motivating -- celebrate each milestone (25%, 50%, 75%, fully funded).

11. **When should you use your emergency fund?** It's for true emergencies -- things that are:
    - Unexpected (you didn't see it coming)
    - Necessary (it must be dealt with now)
    - Urgent (it can't wait until next month)

    A car repair after a breakdown? Emergency. A sale on a TV? Not an emergency. A planned annual expense? That should have its own True Expenses category.

12. If you need to use your emergency fund, don't feel guilty -- this is exactly what it's for. Use `manage_categories` with action="update" to pull from the emergency fund category to cover the expense.

13. After using your emergency fund, prioritize **replenishing** it. Use the same approach as building it: consistent monthly contributions. Read `ynab://budgets/{budget_id}/categories` to see how much you need to get back to your target.

14. Use `manage_categories` with action="update" each month to make your emergency fund contribution. Consider it a non-negotiable line item in your budget, right after your essential expenses.

15. As your financial situation evolves, revisit your target. Got a raise? Your expenses might increase. Paid off debt? Your essential expenses decrease. Use `manage_categories` with action="update" to adjust the goal amount as needed.

16. Read the accounts resource at `ynab://budgets/{budget_id}/accounts` to review where your emergency fund money physically lives. Many people keep it in a high-yield savings account -- still on-budget, just earning a bit of interest.

17. Having a fully funded emergency fund changes your relationship with money. Unexpected expenses become inconveniences rather than crises. You'll sleep better knowing you have months of expenses set aside. Keep going -- every dollar you save brings you closer to that peace of mind!
