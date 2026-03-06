Welcome to YNAB! Let's set up your first budget together. This guide will walk you through every step -- by the end, you'll have a working budget that gives every dollar a job.

1. Read the knowledge resource at `ynab://knowledge/terminology` to understand key YNAB concepts like "To Be Budgeted" (TBB), categories, and the Four Rules before we begin.

2. Use the `manage_budgets` tool with action="list" to see if you already have a budget, or use action="get" to review an existing one at `ynab://budgets/{budget_id}/accounts`.

3. Let's start by adding your **checking account** -- this is usually where your income lands. Use the `manage_accounts` tool with action="create" to add it with type="checking". Enter the current balance as accurately as possible.

4. Next, add your **savings account** if you have one. Use the `manage_accounts` tool with action="create" with type="savings". This should be on-budget so YNAB can help you assign those dollars a purpose.

5. Now let's talk about **on-budget vs off-budget accounts**. On-budget accounts are ones where you want YNAB to manage the money (checking, savings, credit cards). Off-budget accounts are for tracking only (investments, mortgages). Add any remaining on-budget accounts now.

6. If you have credit cards, add them using `manage_accounts` with action="create" and type="creditCard". Enter the current balance as a negative number. Don't worry -- we'll handle the credit card workflow in a moment.

7. Read the categories resource at `ynab://budgets/{budget_id}/categories` to see the default category groups YNAB created for you.

8. Let's customize your categories to match your real life. Use the `manage_categories` tool with action="create_group" to create category groups that make sense for you. Common groups: "Fixed Bills", "Flexible Spending", "Savings Goals", and "Quality of Life".

9. Within each group, use `manage_categories` with action="create" to add specific categories. Start with your most important expenses: rent/mortgage, utilities, groceries, transportation. You can always add more later.

10. Now for the heart of YNAB -- **giving every dollar a job** (Rule 1). Look at your To Be Budgeted (TBB) amount. This is the money sitting in your accounts right now, waiting to be assigned.

11. Use `manage_categories` with action="update" to assign money to your most urgent categories first. Ask yourself: "What does this money need to do before I get paid again?" Fund those categories first.

12. Work through your categories in priority order: immediate obligations first (rent, utilities, food), then upcoming bills, then savings goals. Don't worry about funding everything perfectly right now -- YNAB is flexible.

13. Keep assigning until your TBB reaches zero. If you run out of money before running out of categories, that's completely normal! It just means those categories will wait until your next paycheck.

14. If you added credit card accounts, read the knowledge resource at `ynab://knowledge/credit-cards` now. YNAB handles credit cards differently than you might expect, and understanding this early will save you confusion.

15. Use `manage_months` with action="get" to review your current month's budget. Check that your assigned amounts feel right and your TBB is at or near zero.

16. Great work! You've built your first budget. Here are your next steps:
    - Enter transactions as they happen (or set up import from your bank)
    - Check your budget before making spending decisions
    - When you overspend in a category, move money from another category -- this is Rule 3 ("Roll With the Punches")
    - When your next paycheck arrives, come back and assign those new dollars too

17. Remember: the goal isn't a perfect budget on day one. The goal is awareness of where your money goes. You'll get better at this with every paycheck. You're already ahead just by starting!
