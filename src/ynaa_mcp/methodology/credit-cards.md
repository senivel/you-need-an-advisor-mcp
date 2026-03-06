# Credit Card Handling in YNAB

Credit cards are the most misunderstood part of YNAB. YNAB treats credit card spending fundamentally differently from debit spending, and understanding this model is critical for accurate budgeting guidance.

## How YNAB Treats Credit Cards

When you add a credit card as an on-budget account, YNAB automatically creates a **Credit Card Payment** category in a special "Credit Card Payments" category group. This category tracks how much cash is available to pay the credit card bill.

The key insight: **budgeting happens in spending categories, not the credit card payment category.** When you budget $100 to Groceries and spend $80 on groceries with your credit card, YNAB automatically moves $80 from the Groceries category to the Credit Card Payment category. The money is still "spent" on groceries -- it just hasn't left your checking account yet.

## The Credit Card Payment Category

Each credit card account gets its own payment category. The **Available** amount in this category represents how much cash you have set aside to pay the credit card bill.

This amount increases when:

- You make a budgeted purchase on the credit card (money moves from spending category)
- You budget directly to the payment category (for pre-YNAB debt or interest)

This amount decreases when:

- You make a payment to the credit card (transfer from checking to CC)
- You get a refund on the credit card (money moves back to spending category)

**Ideally, the payment category Available amount equals the credit card account balance** (as a positive number). This means you have enough cash to pay the card in full.

## Budgeting for Credit Card Purchases

When you categorize a credit card transaction:

1. The spending category's **Activity** decreases (you spent from it)
2. The spending category's **Available** decreases
3. The Credit Card Payment category's **Available** increases by the same amount
4. The credit card account balance increases (more debt)

This is automatic -- you never manually move money to the payment category for regular budgeted spending. You budget and categorize exactly the same way whether you use a debit card or credit card.

## Making a Payment

A credit card payment is a **transfer** from your checking account to your credit card account:

- The checking account balance decreases
- The credit card account balance decreases (less debt)
- The Credit Card Payment category Available decreases
- No spending category is affected -- the spending already happened

Categorize payments as a transfer to the credit card account, not as a spending category. YNAB handles the rest.

## Returns and Refunds

When a merchant refunds a credit card purchase:

- The credit card account balance decreases (less debt)
- The Credit Card Payment category Available decreases
- The spending category Available increases (money returned to that category)

Categorize the refund inflow to the same category as the original purchase. The money flows back through the same path.

## Pre-YNAB Debt

If you start YNAB with an existing credit card balance, that balance represents spending that happened before YNAB -- there are no spending categories to pull from.

To handle pre-YNAB debt:

1. Add the credit card with its current balance
2. The Credit Card Payment category will show a **negative Available** amount equal to the debt
3. **Budget directly to the Credit Card Payment category** to cover the pre-YNAB portion
4. You do not need to cover the entire balance immediately -- budget what you can afford to pay

Going forward, new purchases on the card will be covered by their spending categories (the automatic flow). The pre-YNAB debt portion requires direct budgeting to the payment category.

## Interest Charges and Fees

Interest charges and annual fees appear as transactions on the credit card but have no corresponding spending category:

- **Budget directly to the Credit Card Payment category** to cover these charges
- These charges increase your debt without money moving from a spending category
- Alternatively, create a dedicated "Interest & Fees" category and assign the transactions there -- YNAB will then move the money to the payment category automatically

## Common Mistakes

**Budgeting directly to the Credit Card Payment category for regular spending:**
This double-counts the money. When you budget $100 to Groceries and spend it on the card, $100 already moves to the payment category. Budgeting another $100 directly to the payment category means you have set aside $200 for a $100 purchase.

**Ignoring credit overspending:**
When you overspend a category using a credit card, the overspent amount does NOT move to the payment category. This means your payment category will be short -- you are taking on debt without tracking it. See `ynab://knowledge/overspending` for details on how cash vs credit overspending behave differently.

**Not budgeting for pre-YNAB debt:**
If you start with a $3,000 balance and only cover new purchases, the payment category stays $3,000 short. Budget to the payment category over time to eliminate the pre-YNAB portion.

**Treating credit card payments as expenses:**
A payment is a transfer, not an expense. The expense happened when you made the purchase. Categorizing a payment as "Credit Card Payment" spending category (if one exists) would hide where the money actually went.
