Let's build a plan to get out of debt. This workflow will help you understand your full debt picture, choose a payoff strategy, and set up your budget to make consistent progress.

1. Read the knowledge resource at `ynab://knowledge/credit-cards` to understand how YNAB tracks credit card spending and payments. This is essential for managing debt correctly in YNAB.

2. Read the knowledge resource at `ynab://knowledge/overspending` to understand the difference between cash overspending and credit overspending, and why it matters for your debt payoff plan.

3. Read the accounts resource at `ynab://budgets/{budget_id}/accounts` to identify all your debt accounts -- credit cards, personal loans, auto loans, student loans, or any other liabilities.

4. Let's take stock of where you are. For each debt account, note: the current balance, the interest rate (if you know it), and the minimum monthly payment. Don't let the total number overwhelm you -- having a clear picture is the first step to making progress.

5. Check for any **cash overspending** in your current month. Use `manage_months` with action="get" to review your budget. If any categories show cash overspending (red in the Available column), address these first -- cash overspending means you've spent money you don't actually have, and it will increase your debt.

6. Use `manage_categories` with action="update" to cover any cash overspending by moving money from other categories. This stops the bleeding before we focus on payoff.

7. Now let's choose your debt payoff strategy. There are two proven approaches:

   **Avalanche method**: Pay minimums on everything, then put extra money toward the debt with the **highest interest rate**. This saves the most money over time.

   **Snowball method**: Pay minimums on everything, then put extra money toward the debt with the **smallest balance**. This gives you quick wins that build momentum.

   Both work. The avalanche method is mathematically optimal. The snowball method is psychologically powerful. Choose the one you'll stick with.

8. Use `manage_categories` with action="create_group" to create a "Debt Payments" category group. This keeps all your debt-related budgeting organized and visible.

9. Within that group, use `manage_categories` with action="create_category" to create a category for each debt. Name them clearly (e.g., "Visa Payment", "Car Loan Payment").

10. Set up scheduled transactions for your minimum payments. Use `manage_scheduled_transactions` with action="create" for each debt's minimum monthly payment. This ensures you never miss a payment.

11. Now for the extra payments. Look at your budget and identify any money you can direct toward your target debt (the one you chose in step 7 based on your strategy). Even small extra amounts make a real difference over time.

12. Use `manage_categories` with action="update" to budget your extra payment amount to the target debt's category each month.

13. Read the categories resource at `ynab://budgets/{budget_id}/categories` to review your debt categories and make sure your payment amounts look right.

14. When you make a payment on a credit card, YNAB automatically moves the budgeted amount to the credit card's payment category. For non-credit-card debt (loans), use `manage_transactions` with action="create" to record each payment.

15. Each month when you get paid, follow this order:
    - Fund immediate living expenses first
    - Fund all minimum debt payments (your scheduled transactions handle this)
    - Put any remaining money toward your target debt
    - When the target debt is paid off, roll that payment amount into the next debt on your list

16. Track your progress monthly. Use `manage_accounts` with action="list" to see your debt balances going down. Celebrate each milestone -- every payment is progress.

17. If unexpected money comes in (tax refund, bonus, side income), consider putting a portion toward your target debt. You don't have to put all of it there -- balance debt payoff with living your life.

18. You've got a solid plan in place. Stay consistent, keep budgeting every dollar, and remember: getting out of debt is a marathon, not a sprint. Every month you're making progress, and that's what matters.
