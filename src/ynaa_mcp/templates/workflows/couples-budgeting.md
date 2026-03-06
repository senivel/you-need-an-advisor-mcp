Budgeting as a couple is one of the most impactful financial moves you can make together. This guide will help you set up a shared budget structure and establish a workflow for ongoing money conversations.

1. Read the knowledge resource at `ynab://knowledge/terminology` to make sure you're both on the same page with YNAB concepts. Having shared vocabulary (TBB, categories, envelopes) makes budget conversations smoother.

2. Before we touch any settings, let's talk structure. There are three common approaches to shared finances:
   - **Fully shared**: All income goes into one pot, all expenses are budgeted together
   - **Yours/Mine/Ours**: Each partner keeps personal accounts plus a shared account for joint expenses
   - **Proportional split**: Shared expenses are split proportionally based on income

   Choose the approach that fits your relationship. There's no wrong answer -- the best system is the one you'll both use.

3. Read the accounts resource at `ynab://budgets/{budget_id}/accounts` to see what accounts are currently in the budget.

4. Add any accounts that aren't in the budget yet. Use `manage_accounts` with action="create" for each account. If you're doing a "Yours/Mine/Ours" setup, make sure each partner's personal accounts and the shared account are all included.

5. Use `manage_categories` with action="create_group" to create category groups that reflect your shared structure. Common groups for couples:
   - "Shared Fixed Expenses" (rent/mortgage, utilities, insurance)
   - "Shared Flexible Spending" (groceries, household items, dining out together)
   - "Partner 1 Personal" (individual spending)
   - "Partner 2 Personal" (individual spending)
   - "Shared Goals" (vacation, emergency fund, home down payment)

6. Within each group, use `manage_categories` with action="create" to add specific categories. Start with the ones you both agree on -- you can always refine later.

7. Here's the key to reducing friction: **fun money categories**. Use `manage_categories` with action="create" to create a personal allowance category for each partner. This is money each person can spend however they want, no questions asked. It's not about control -- it's about freedom within structure.

8. Decide on the fun money amount together. It should be equal (or proportional if your incomes differ significantly). Budget it using `manage_categories` with action="update". This one category prevents more arguments than any other.

9. Now let's set up your **budget meeting** workflow. This is a regular time (weekly or bi-weekly) where you sit down together and:
   - Review what's been spent since last meeting
   - Discuss upcoming expenses
   - Make category adjustments together
   - Celebrate progress toward shared goals

10. Use `manage_months` with action="get" to pull up the current month's budget during your meeting. Review each category group together.

11. Read the categories resource at `ynab://budgets/{budget_id}/categories` to check category balances. Look for categories that are running low and discuss whether to move money or adjust spending for the rest of the month.

12. Common friction points and how to handle them:
    - **Different spending priorities**: This is normal. The budget meeting is where you negotiate. Neither person should feel like the other is making all the decisions.
    - **One partner overspends a category**: Move money from another category together. No blame -- this is Rule 3 (Roll With the Punches). Discuss whether the category needs more funding next month.
    - **Surprise expenses**: If something comes up, discuss it at the next budget meeting. The fun money categories give each person flexibility for small surprises.

13. For income that arrives at different times (e.g., one partner is paid bi-weekly, the other monthly), budget each paycheck as it arrives. Use `manage_categories` with action="update" to assign dollars to the highest-priority unfunded categories first.

14. Set up recurring shared bills as scheduled transactions using `manage_scheduled_transactions` with action="create". This way both partners can see what's coming up and when.

15. Track your progress toward shared goals using `manage_categories` with action="get" to check goal progress. Celebrating milestones together (emergency fund hit $1,000, vacation fund is half full) makes budgeting feel like a team effort.

16. Use `manage_accounts` with action="list" periodically to review your overall financial picture together. Watching your net worth grow as a team is powerful motivation.

17. Remember: the budget isn't a set of rules one partner imposes on the other. It's a shared plan that you build and adjust together. The more you communicate about money, the easier it gets. You're building something great together!
