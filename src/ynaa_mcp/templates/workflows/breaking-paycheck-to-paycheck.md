Breaking the paycheck-to-paycheck cycle is one of the most transformative things you can do with YNAB. The goal: get to a point where this month's bills are paid with last month's income. Let's build a plan to get there.

1. Read the knowledge resource at `ynab://knowledge/terminology` to understand the **Age of Money** concept. Age of Money tells you, on average, how many days your dollars sit in your budget before being spent. When it's consistently over 30 days, you're living on last month's income.

2. Read the accounts resource at `ynab://budgets/{budget_id}/accounts` to see your current cash position. Don't worry about the numbers right now -- we're establishing a starting point.

3. Read the categories resource at `ynab://budgets/{budget_id}/categories` to understand your current budget structure. We'll be working within this structure to free up money for aging.

4. The concept is simple: instead of getting paid and immediately budgeting that money for this month's expenses, you want to get paid and hold that money until next month. This means **this month's expenses are already covered** before the month even starts.

5. Use `manage_categories` with action="create_category" to create a "Buffer" or "Next Month's Budget" category. This is the holding tank for income that you won't touch until the following month.

6. Let's be real: you probably can't buffer a full month overnight. That's fine. We're going to get there gradually. Here's the transition plan:

7. **Phase 1 -- Find the margin.** Look at your current budget and identify categories where you can temporarily reduce spending. Use `manage_categories` with action="list" to review everything. Common places to find margin:
   - Dining out / takeout
   - Entertainment / subscriptions
   - Shopping / clothing
   - Any category where you tend to overspend

8. Use `manage_categories` with action="update" to slightly reduce the budgeted amounts in those categories. Redirect the difference to your Buffer category. Even $50-100/month matters here.

9. **Phase 2 -- Start aging your money.** When your next paycheck arrives, try to put a portion into the Buffer instead of budgeting it all for immediate expenses. Any amount counts -- even 10% of your paycheck is progress.

10. Use `manage_months` with action="get" each week to check in on your budget. Are you staying within the reduced category amounts? If not, adjust -- this is an iterative process, not a one-time setup.

11. **Phase 3 -- Milestone tracking.** As your buffer grows, celebrate the milestones:
    - **1 week ahead**: You could cover a week of expenses without any income. That's huge!
    - **2 weeks ahead**: You're halfway to a full month's buffer.
    - **Full month ahead**: You've broken the cycle. This month's bills are fully covered before the month starts.

12. When your Buffer category has a full month of expenses saved, here's how to deploy it: at the start of a new month, use `manage_categories` with action="update" to move the Buffer money to TBB, then budget your entire month in one sitting. This is what living on last month's income feels like.

13. If unexpected expenses knock you backward, don't panic. Use `manage_categories` with action="update" to cover the expense from wherever makes sense. Your buffer might shrink temporarily -- that's what it's there for. Resume building it with your next paycheck.

14. **Accelerators** -- ways to speed up the process:
    - Use any windfalls (tax refund, bonus, side income) to top up the buffer
    - Try a no-spend challenge for a week and redirect the savings
    - Sell items you no longer need
    - Pick up temporary extra work if you're motivated

15. Keep checking your Age of Money as a health metric. Use `manage_budgets` with action="get" to see it. As you build your buffer, you'll watch the age climb from days to weeks to over 30 days. It's one of the most satisfying numbers in YNAB.

16. **Long-term maintenance.** Once your buffer is established, the monthly workflow becomes simple:
    - Income arrives -> goes into Buffer category
    - First of the month -> move Buffer to TBB -> budget the whole month
    - Repeat

17. Living on last month's income means you never wonder "Can I afford this bill?" because the money is already there. Paydays become calm instead of urgent. Bills arrive and you shrug because they're already covered. That's the feeling we're building toward -- and every dollar you save gets you closer. You can do this!
