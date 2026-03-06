Budgeting with irregular income can feel uncertain, but YNAB is actually built for this. The core principle is simple: only budget money you actually have right now. Let's set up a system that brings stability to an unpredictable income.

1. Read the knowledge resource at `ynab://knowledge/terminology` to ground yourself in YNAB's key concepts, especially "To Be Budgeted" (TBB) and Rule 1: Give Every Dollar a Job. These are particularly important for irregular income.

2. Read the categories resource at `ynab://budgets/{budget_id}/categories` to see your current budget structure. We'll be adding some categories specifically designed for income smoothing.

3. The core concept for irregular income is the **income buffer** -- also sometimes called "Income Replacement." The goal is to live on last month's income so you always know exactly how much you have to budget, regardless of when this month's money arrives.

4. Use `manage_categories` with action="create_group" to create a group called "Income Buffer" (or "Income Replacement" -- whatever name resonates with you).

5. Use `manage_categories` with action="create" to create a category within that group called "Next Month's Budget." This is where you'll hold money until it's time to budget it.

6. Here's how the monthly workflow works:
   - When income arrives (a client payment, a commission check, freelance invoice), categorize it as income in YNAB
   - Instead of budgeting it immediately for this month's expenses, assign it to "Next Month's Budget"
   - At the start of the next month, move money from "Next Month's Budget" to TBB and budget your month normally

7. If you're not able to buffer a full month yet, that's completely fine. Start by budgeting only what you have right now for your most critical expenses. Each time income arrives, budget the next most important thing. This is YNAB working exactly as designed.

8. To build your buffer over time, look for categories where you can temporarily reduce spending. Use `manage_categories` with action="list" to review your budget and identify opportunities. Even redirecting small amounts toward the buffer category adds up.

9. Now let's handle **true expenses** -- those irregular annual or semi-annual costs that catch freelancers off guard. Things like annual software subscriptions, quarterly tax payments, insurance premiums, or professional dues.

10. Use `manage_categories` with action="create" to create categories for each true expense. Calculate the monthly amount (annual cost divided by 12) and budget that amount each month so the money is ready when the bill comes.

11. For **quarterly estimated tax payments** (common for freelancers), create a "Taxes" category and set aside a percentage of each payment you receive. A common starting point is 25-30% of income, but check with your tax advisor.

12. Let's address the feast-and-famine cycle. During good months (feast), resist the urge to inflate your lifestyle. Instead:
    - Fund your buffer category first
    - Top up your true expense categories
    - Then allocate to quality-of-life categories

13. During lean months (famine), your buffer does the heavy lifting. If the buffer isn't full yet, prioritize ruthlessly: housing, food, utilities, transportation, then everything else. Use `manage_categories` with action="update" to move money between categories as needed.

14. Set up any predictable recurring expenses as scheduled transactions using `manage_scheduled_transactions` with action="create". Even with irregular income, many expenses are predictable (rent, subscriptions, insurance).

15. Review your budget weekly rather than monthly. Use `manage_months` with action="get" to check your current month's status. Frequent check-ins are especially important with irregular income because your picture changes every time money comes in.

16. Use the accounts resource at `ynab://budgets/{budget_id}/accounts` to monitor your overall cash position. As your buffer grows, you'll notice something wonderful: the stress of "when will the next payment arrive?" starts to fade.

17. Your target is a full month's buffer -- enough that you could budget all of next month's expenses right now. It might take a few months to get there, and that's normal. Each paycheck that goes to the buffer brings you closer to financial predictability, even with an unpredictable income. You've got this!
