# Scheduled Transaction Tools

Scheduled transactions represent your recurring and upcoming financial commitments -- rent, subscriptions, loan payments, regular transfers. These tools let you view, create, update, and manage scheduled transactions so you always know what's coming up and can plan ahead.

In YNAB, scheduled transactions automatically create real transactions on their due dates. Setting them up means you'll never forget a bill and your budget always reflects upcoming obligations.

## Usage Examples

> **You:** What recurring transactions do I have?
>
> **Claude** calls `manage_scheduled_transactions` with action `list` and responds:
>
> _6 scheduled transactions found:_
> _- 2026-04-01 | Landlord | -$1,500.00 | Rent [monthly]_
> _- 2026-03-15 | Netflix | -$22.99 | Subscriptions [monthly]_
> _- 2026-03-20 | Electric Company | -$120.00 | Utilities [monthly]_
> _- 2026-04-01 | Gym | -$49.99 | Health [monthly]_
> _- 2026-03-14 | Employer Inc | $3,200.00 | Income [everyOtherWeek]_
> _- 2026-06-15 | Insurance Co | -$600.00 | Insurance [twiceAYear]_

> **You:** Tell me more about my rent payment.
>
> **Claude** calls `manage_scheduled_transactions` with action `get` and responds:
>
> _Scheduled Transaction: Landlord_
> _Amount: -$1,500.00_
> _Frequency: monthly_
> _Next date: 2026-04-01_
> _Account: Checking_
> _Category: Rent_
> _Memo: April rent_

> **You:** Schedule a new monthly payment of $50 to my gym starting April 1st.
>
> **Claude** calls `manage_scheduled_transactions` with action `create`:
>
> _Scheduled transaction created:_
> _- Gym Membership | -$50.00 | monthly starting 2026-04-01_

> **You:** Cancel my Netflix subscription in YNAB.
>
> **Claude** calls `manage_scheduled_transactions` with action `delete`:
>
> _Scheduled transaction deleted: Netflix ($22.99/month)_

## Available Actions

| Action   | Description                                      |
| -------- | ------------------------------------------------ |
| `list`   | List all scheduled transactions                  |
| `get`    | Get details for a specific scheduled transaction |
| `create` | Create a new scheduled/recurring transaction     |
| `update` | Update an existing scheduled transaction         |
| `delete` | Delete a scheduled transaction                   |

---

## API Reference

<!-- prettier-ignore -->
::: ynaa_mcp.tools.scheduled.manage_scheduled_transactions
    options:
      show_root_heading: true
      show_source: true
