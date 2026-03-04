# Converters

YNAB stores all monetary amounts as **milliunits** -- 1 dollar equals 1,000 milliunits. The converters module handles translation between YNAB's internal format and human-readable dollar amounts.

## Why Milliunits?

YNAB uses integer milliunits to avoid floating-point precision issues. For example, `$45.67` is stored as `45670` milliunits. This is a common pattern in financial APIs (Stripe uses cents, YNAB uses milliunits).

## Boundary Conversion

Conversion happens at the **boundary** -- the `YNABClient` layer:

- **Inbound (API responses):** The client recursively walks response data and converts milliunit fields to dollar floats before any tool sees the data
- **Outbound (API requests):** Tools call `dollars_to_milliunits()` when sending write requests (creating accounts, setting budgets)

This means tool functions always work with dollars. They never need to know about milliunits.

## Decimal Precision

All intermediate arithmetic uses `decimal.Decimal` to avoid IEEE 754 floating-point drift:

- `milliunits_to_dollars`: `Decimal(milliunits) / 1000`
- `dollars_to_milliunits`: `Decimal(str(dollars)) * 1000` with `ROUND_HALF_UP`

The `str()` wrapper in `dollars_to_milliunits` is deliberate -- `Decimal(0.1)` produces `0.1000000000000000055511151231257827021181583404541015625`, while `Decimal("0.1")` produces exactly `0.1`.

## API Reference

::: ynab_mcp.converters
options:
show_root_heading: true
show_source: true
members_order: source
