# Goal Types in YNAB

Goals help automate budgeting by telling YNAB how much money a category needs. When a goal is set, YNAB calculates whether the category is **funded**, **underfunded**, or **overfunded** relative to the goal, and the "Underfunded" button can auto-assign the right amount.

## Current Goal Types

YNAB's current goal system uses three types, identified by the `goal_type` API field:

### Target Category Balance (`goal_type: "TB"`)

Save up to a specific total amount, optionally by a target date.

- **Without a date:** Build the balance over time at your own pace. YNAB shows the category as underfunded if the balance is below the target.
- **With a target date** (`goal_target_month`): YNAB calculates the monthly amount needed to reach the target by that month, spreading the remaining amount evenly across remaining months.

**API fields:**

- `goal_target` -- The target balance amount in milliunits (see `ynab://knowledge/terminology` for milliunits explanation)
- `goal_target_month` -- Target date in `YYYY-MM-DD` format (first of the month), or `null` if no date
- `goal_percentage_complete` -- How close the current balance is to the target (0-100+)
- `goal_months_to_budget` -- Months remaining until the target date
- `goal_under_funded` -- Amount in milliunits still needed this month to stay on track

**Use cases:**

- Emergency fund (TB, no date): "Save $10,000 whenever I can"
- Vacation fund (TB, with date): "Save $3,000 by June 2025"
- Down payment (TB, with date): "Save $50,000 by December 2026"

### Monthly Savings Builder (`goal_type: "MF"`)

Budget a fixed amount every single month, regardless of what is already in the category.

- The category is underfunded if less than the target has been budgeted **this month**
- Existing balance does not reduce the needed amount -- this goal is about consistent monthly contributions
- Rolling over unused funds does not affect next month's goal

**API fields:**

- `goal_target` -- The monthly funding amount in milliunits
- `goal_under_funded` -- Difference between target and what has been budgeted this month
- `goal_percentage_complete` -- Budgeted this month divided by target (0-100+)

**Use cases:**

- Retirement contributions: "Budget $500 every month"
- Charitable giving: "Set aside $200 monthly"
- Regular savings: "Add $1,000 to savings each month"

### Needed for Spending / Spending Target (`goal_type: "NEED"`)

Plan to spend a specific amount, with the category resetting by a target date.

- **Monthly cadence** (target month is the current month or repeating): Budget the target amount each month for recurring expenses
- **By-date cadence** (target month is in the future): Spread the needed amount across months until the target date, similar to TB but for spending rather than saving
- The key difference from TB: NEED goals expect the money to be **spent**, not accumulated

**API fields:**

- `goal_target` -- The spending target amount in milliunits
- `goal_target_month` -- When the spending will occur
- `goal_under_funded` -- Amount still needed to fully fund the goal
- `goal_months_to_budget` -- Months remaining to spread the funding
- `goal_percentage_complete` -- Funding progress toward the target

**Use cases:**

- Rent/mortgage (NEED, monthly): "I need $1,500 for rent each month"
- Insurance premium (NEED, by date): "I need $600 for insurance by July"
- Annual subscriptions (NEED, by date): "I need $120 for this service by renewal date"

## The Underfunded Calculation

Each goal type calculates `goal_under_funded` differently:

- **TB without date:** `goal_target - category_balance` (simple gap to target)
- **TB with date:** `(goal_target - category_balance) / goal_months_to_budget` (spread evenly)
- **MF:** `goal_target - budgeted_this_month` (ignores existing balance)
- **NEED monthly:** `goal_target - budgeted_this_month` (similar to MF for monthly)
- **NEED by date:** `(goal_target - category_balance) / goal_months_to_budget` (similar to TB with date)

The **Underfunded button** in YNAB's UI assigns `goal_under_funded` milliunits to the category from TBB. This is the recommended way to fund goals consistently.

When `goal_under_funded` is `0`, the category is fully funded for the current period. When `goal_percentage_complete` exceeds 100, the category is overfunded relative to the goal.

## Setting and Adjusting Goals

- **One goal per category** -- Each category can have at most one active goal
- **Changing a goal type** replaces the previous goal entirely
- **Removing a goal** does not affect the category's current balance or budgeted amount -- it only removes the funding guidance
- **Changing the target amount** recalculates underfunded immediately for the current month
- **Moving the target date** redistributes the remaining needed amount across the new timeframe

## API Goal Fields Reference

| Field                      | Type                                   | Description                                |
| -------------------------- | -------------------------------------- | ------------------------------------------ |
| `goal_type`                | `"TB"` \| `"MF"` \| `"NEED"` \| `null` | Goal type, or null if no goal set          |
| `goal_target`              | integer (milliunits)                   | Target amount                              |
| `goal_target_month`        | string \| null                         | Target date (`YYYY-MM-DD`, first of month) |
| `goal_percentage_complete` | integer                                | Funding progress (0-100+)                  |
| `goal_months_to_budget`    | integer                                | Months remaining to target date            |
| `goal_under_funded`        | integer (milliunits)                   | Amount still needed this period            |
| `goal_overall_funded`      | integer (milliunits)                   | Total funded toward the goal               |
| `goal_overall_left`        | integer (milliunits)                   | Total remaining to reach the goal          |

These fields appear on category objects in the API response. Categories without goals have `goal_type: null` and all goal fields as `null` or `0`.
