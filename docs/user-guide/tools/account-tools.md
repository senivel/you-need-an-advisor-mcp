# Account Tools

Accounts are where your money lives -- checking, savings, credit cards, cash, investment tracking, and more. Account tools let you see your balances at a glance, drill into individual account details, and create new accounts without leaving the conversation.

In YNAB, accounts fall into two categories: **on-budget** accounts (checking, savings, credit cards) where every dollar gets a job, and **tracking** accounts (investments, mortgages) that you monitor but don't budget from. This distinction matters when you're looking at your overall financial picture versus your day-to-day budget.

## Usage Examples

> **You:** Show me my accounts.
>
> **Claude** calls `manage_accounts` with action `list` and responds:
>
> _4 open accounts found:_
> _- Checking (checking) -- Balance: $2,450.00_
> _- Savings (savings) -- Balance: $8,200.00_
> _- Visa (creditCard) -- Balance: -$1,340.00_
> _- Cash (cash) -- Balance: $45.00_

> **You:** Tell me about my Visa account.
>
> **Claude** calls `manage_accounts` with action `get` and responds:
>
> _Account: Visa_
> _Type: creditCard_
> _On budget: Yes_
> _Balance: -$1,340.00_
> _Cleared balance: -$1,200.00_
> _Uncleared balance: -$140.00_

> **You:** I want to include closed accounts too.
>
> **Claude** calls `manage_accounts` with action `list` and `include_closed=true`:
>
> _6 accounts found (including closed):_
> _- Checking (checking) -- Balance: $2,450.00_
> _- Old Savings (savings) -- Balance: $0.00 [closed]_
> _..._

> **You:** Create a new savings account called Emergency Fund with $1,000.
>
> **Claude** calls `manage_accounts` with action `create`, converting dollars to YNAB milliunits automatically:
>
> _Account created: Emergency Fund_
> _Type: savings_
> _Starting balance: $1,000.00_

## Available Actions

| Action   | Description                                                        |
| -------- | ------------------------------------------------------------------ |
| `list`   | List all accounts in a budget (open by default, optionally closed) |
| `get`    | Get detailed info about a specific account                         |
| `create` | Create a new account with a name, type, and starting balance       |

---

## API Reference

<!-- prettier-ignore -->
::: ynaa_mcp.tools.accounts.manage_accounts
    options:
      show_root_heading: true
      show_source: true
