"""Milliunit-to-dollar and dollar-to-milliunit conversion utilities.

YNAB uses "milliunits" internally -- 1 dollar = 1000 milliunits.
All intermediate arithmetic uses ``decimal.Decimal`` to avoid
IEEE 754 floating-point drift (e.g., ``0.1 + 0.2 != 0.3``).
"""

from decimal import ROUND_HALF_UP, Decimal


MILLIUNIT_FACTOR = Decimal(1000)
"""Conversion factor between dollars and YNAB milliunits."""


def milliunits_to_dollars(milliunits: int) -> float:
    """Convert YNAB milliunits to a dollar amount.

    Args:
        milliunits: Amount in YNAB milliunits (1000 milliunits = $1.00).

    Returns:
        The equivalent dollar amount as a float.

    Examples:
        >>> milliunits_to_dollars(45670)
        45.67
        >>> milliunits_to_dollars(-10000)
        -10.0
    """
    return float(Decimal(milliunits) / MILLIUNIT_FACTOR)


def dollars_to_milliunits(dollars: float) -> int:
    """Convert a dollar amount to YNAB milliunits.

    Uses ``Decimal(str(dollars))`` to avoid floating-point precision issues,
    then rounds to the nearest milliunit using ROUND_HALF_UP.

    Args:
        dollars: Dollar amount to convert.

    Returns:
        The equivalent amount in YNAB milliunits as an integer.

    Examples:
        >>> dollars_to_milliunits(45.67)
        45670
        >>> dollars_to_milliunits(0.1 + 0.2)
        300
    """
    result = Decimal(str(dollars)) * MILLIUNIT_FACTOR
    return int(result.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def format_dollars(amount: float) -> str:
    """Format a dollar amount with $ symbol and comma separators.

    Args:
        amount: Dollar amount (already converted from milliunits).

    Returns:
        Formatted string like "$1,234.56" or "-$1,234.56".

    Examples:
        >>> format_dollars(1234.56)
        '$1,234.56'
        >>> format_dollars(-50.0)
        '-$50.00'
        >>> format_dollars(0.0)
        '$0.00'
    """
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


_YYYY_MM_LENGTH = 7


def normalize_month(month: str | None) -> str:
    """Normalize a month parameter for the YNAB API.

    Accepts ``"YYYY-MM"``, ``"YYYY-MM-DD"``, or ``None`` (current month).

    Args:
        month: Month string or None for current month.

    Returns:
        ``"current"`` or ``"YYYY-MM-01"`` format string.

    Examples:
        >>> normalize_month(None)
        'current'
        >>> normalize_month("2026-03")
        '2026-03-01'
        >>> normalize_month("2026-03-01")
        '2026-03-01'
    """
    if month is None:
        return "current"
    if len(month) == _YYYY_MM_LENGTH:
        return f"{month}-01"
    return month
