Create a debt payoff plan.

1. Read `ynab://knowledge/credit-cards` to understand how YNAB handles credit card debt, including the Credit Card Payment category, budgeting for purchases on credit, and the distinction between new spending and pre-YNAB debt.

2. Read `ynab://knowledge/overspending` to understand how overspending on credit cards creates additional debt and how cash vs credit overspending behave differently in YNAB.

3. Use the `manage_budgets` tool with action="get" and budget_id="{budget_id}" to get the budget summary and current To Be Budgeted amount.

4. Use the `manage_accounts` tool with action="list" and budget_id="{budget_id}" to identify all debt accounts:
   - Credit card accounts (type: creditCard) -- note the balance of each.
   - Loan/mortgage accounts if tracked (type: otherLiability) -- note balances.
   - Record the account name, current balance, and type for each.

5. For each credit card, use the `manage_categories` tool with action="list" and budget_id="{budget_id}" to find the corresponding Credit Card Payment category. Note the budgeted amount vs the available amount to understand how much is allocated for payment.

6. Gather interest rate information. Ask the user for the interest rate (APR) on each debt, as YNAB does not store interest rates. Create a summary table:
   - Debt name / account
   - Current balance
   - Interest rate (APR)
   - Minimum monthly payment
   - Credit Card Payment category balance (for credit cards)

7. Calculate the total debt across all accounts. Present this clearly -- seeing the full picture is the first step.

8. **Avalanche Strategy** (mathematically optimal):
   - Order debts from highest interest rate to lowest.
   - Pay minimums on all debts.
   - Put all extra money toward the highest-interest debt.
   - When that debt is paid off, roll its payment into the next highest-interest debt.
   - **Trade-off**: Saves the most money in interest over time. May take longer to see a debt fully eliminated, which can feel discouraging.

9. **Snowball Strategy** (psychologically motivating):
   - Order debts from smallest balance to largest.
   - Pay minimums on all debts.
   - Put all extra money toward the smallest-balance debt.
   - When that debt is paid off, roll its payment into the next smallest debt.
   - **Trade-off**: Creates quick wins that build momentum. May cost more in total interest compared to avalanche.

10. Present a side-by-side comparison for the user's specific debts:
    - Estimated months to debt-free under each strategy.
    - Estimated total interest paid under each strategy.
    - Which debt gets eliminated first under each strategy.

11. Help the user choose a strategy based on their situation:
    - If interest rate differences are small (within 2-3%), snowball may be better for motivation.
    - If one debt has a significantly higher rate, avalanche saves meaningful money.
    - Either strategy is far better than paying only minimums.

12. Once a strategy is chosen, set up the budget categories using the `manage_categories` tool with action="update" and budget_id="{budget_id}":
    - Set minimum payment amounts as budgeted amounts for each Credit Card Payment category.
    - Set a target or monthly savings goal on the priority debt category for the extra payment amount.

13. Address new spending on credit cards:
    - In YNAB, budgeted spending on credit cards automatically moves money to the Credit Card Payment category.
    - The key is to budget for purchases in spending categories before making them on credit.
    - Unbudgeted credit card spending creates new debt -- emphasize this distinction.

14. Plan for preventing new debt:
    - Review spending categories to ensure they are adequately funded.
    - If categories are consistently overspent on credit, the budget amounts need adjustment.
    - Consider using the `spending_trends` prompt to identify problem categories.

15. Set up a review schedule:
    - Monthly: Check progress against the payoff plan.
    - Use the `manage_accounts` tool with action="get" to track declining balances.
    - Celebrate milestones -- each debt eliminated is a significant achievement.
    - Revisit the plan if income or expenses change significantly.
