Analyze spending trends across multiple months.

1. Use the `manage_budgets` tool with action="get" and budget_id="{budget_id}" to confirm the budget exists and note the current month.

2. Determine the 3-month analysis window: current month and the 2 prior months. Format each as YYYY-MM-DD (first of month).

3. Use the `manage_months` tool with action="get" and budget_id="{budget_id}" for each of the 3 months to retrieve month-level summaries including income, budgeted, activity, and To Be Budgeted.

4. Use the `manage_transactions` tool with action="list" and budget_id="{budget_id}" with since_date set to the first day of the earliest month to fetch all transactions across the 3-month window.

5. Group transactions by month and category. For each category, calculate total spending per month.

6. Identify categories with **increasing spending trends** -- where each successive month shows higher spending than the prior. Flag these as potential budget pressure points.

7. Identify categories with **decreasing spending trends** -- where spending has dropped month over month. Note these as areas of improvement or reduced need.

8. Flag categories that are **consistently over budget** across all 3 months. These represent structural budget misalignments where the budgeted amount does not match actual spending patterns.

9. Calculate month-over-month percentage changes for the top 10 categories by total spending:
   - Month 1 to Month 2: percentage change
   - Month 2 to Month 3: percentage change
   - Overall trend direction (increasing, decreasing, stable)

10. Identify any **anomalous spending** -- categories where one month's spending is more than double or less than half of the other two months. These may indicate one-time expenses or irregular billing.

11. Compare total income across the 3 months. Note whether income is stable, growing, or declining, as this affects how spending trends should be interpreted.

12. Calculate the spending-to-income ratio for each month. A rising ratio (even with stable income) indicates growing financial pressure.

13. Use the `manage_categories` tool with action="list" and budget_id="{budget_id}" to get current budgeted amounts and compare them against average actual spending over the 3-month period. Highlight categories where the budget is more than 20% off from the spending average.

14. Look for seasonal or cyclical patterns. Some categories (utilities, gifts, insurance) may have predictable variations that are not true trends.

15. Compile findings into a structured report:

    **Trend Summary**
    - Overall spending direction (increasing, decreasing, stable)
    - Total spending by month with percentage changes
    - Income vs spending ratio trend

    **Category Deep Dives**
    - Top 5 categories with largest spending increases
    - Top 5 categories with largest spending decreases
    - Categories consistently over budget (structural misalignment)
    - Anomalous spending events

    **Recommendations**
    - Categories where budget amounts should be adjusted to match reality
    - Areas where spending reduction would have the most impact
    - Suggestions for using the `budget_health_analysis` prompt to assess current month impact
