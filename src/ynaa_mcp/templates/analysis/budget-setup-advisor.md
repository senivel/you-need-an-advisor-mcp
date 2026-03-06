Guide through setting up a new YNAB budget.

1. Read `ynab://knowledge/terminology` to understand core YNAB concepts: milliunits, on-budget vs off-budget accounts, To Be Budgeted, the Four Rules, and transaction states. Use this knowledge throughout the setup process.

2. Use the `manage_budgets` tool with action="get" and budget_id="{budget_id}" to see the current state of the budget -- whether it is brand new or partially configured.

3. Read the accounts resource at `ynab://budgets/{budget_id}/accounts` to check if any accounts have been added yet.

4. **Set up accounts.** Walk through adding accounts in this order:
   - **Checking accounts**: Use the `manage_accounts` tool with action="create" and budget_id="{budget_id}". Set type to "checking" and provide the current balance. This is where most day-to-day money lives.
   - **Savings accounts**: Same process with type="savings". Explain that in YNAB, savings accounts are on-budget -- the money is assigned to categories, not hidden away.
   - **Credit cards**: Use action="create" with type="creditCard". Enter the current balance as a negative number (amount owed). Explain that YNAB creates a special Credit Card Payment category automatically.

5. Reassure the user: it is normal to feel overwhelmed at this stage. YNAB's approach is different from traditional budgeting, and it gets easier with practice.

6. Read the categories resource at `ynab://budgets/{budget_id}/categories` to see the default category groups YNAB has created.

7. **Organize category groups.** Guide through creating a category structure using the `manage_categories` tool:
   - Use action="create_group" to create groups if needed. Recommended groups:
     - Immediate Obligations (rent/mortgage, utilities, groceries, transport, minimum debt payments)
     - True Expenses (insurance premiums, car maintenance, medical costs, annual subscriptions)
     - Quality of Life (dining out, entertainment, hobbies, personal care)
     - Savings Goals (emergency fund, vacation, large purchases)
   - Use action="create" within each group for specific categories.

8. Explain Rule 1: **Give Every Dollar a Job.** Every dollar currently in the accounts needs to be assigned to a category. This is not about predicting the future -- it is about deciding what today's dollars should do.

9. **Initial budget allocation.** Walk through assigning money using the `manage_categories` tool with action="update" to set budgeted amounts:
   - Start with immediate obligations due before the next paycheck.
   - Only budget money that is actually available (the TBB amount).
   - Do not budget for the entire month if the money is not there yet -- budget what is available now and assign more when the next paycheck arrives.

10. Use the `manage_budgets` tool with action="get" to verify the To Be Budgeted amount reaches zero after allocation. If it is still positive, guide the user to assign the remaining dollars. If negative, help identify where to pull back.

11. Explain Rule 2: **Embrace Your True Expenses.** Help identify large, non-monthly expenses (car insurance every 6 months, holiday gifts annually) and set up monthly savings targets in the True Expenses group.

12. For each True Expenses category, use the `manage_categories` tool with action="update" to set appropriate goal types:
    - Monthly Savings Builder for recurring annual/semi-annual costs.
    - Target Category Balance for specific savings targets.

13. Explain Rule 3: **Roll With the Punches.** Budgets are living documents. When overspending happens (and it will), the right response is to move money between categories, not to feel like the budget failed. This is normal and expected.

14. Explain Rule 4: **Age Your Money.** The long-term goal is to spend money that is at least 30 days old, meaning this month's spending comes from last month's income. This happens naturally over time and should not be forced.

15. **Next steps after setup:**
    - Enter transactions as they happen (or set up bank import).
    - Check the budget before making purchases to see what is available in each category.
    - When the next paycheck arrives, assign those new dollars starting with the most pressing needs.
    - Consider running the `budget_health_analysis` prompt in a week to check on progress.
