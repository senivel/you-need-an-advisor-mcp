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
