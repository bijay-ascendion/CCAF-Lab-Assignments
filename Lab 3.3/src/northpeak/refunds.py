"""Refund eligibility and amounts for NorthPeak Outfitters."""

from __future__ import annotations

# A return is eligible within this many days of delivery.
RETURN_WINDOW_DAYS = 30


def within_return_window(days_since_delivery: int) -> bool:
    """Return True if a return is still inside the 30-day window."""
    if days_since_delivery < 0:
        raise ValueError("days_since_delivery must not be negative")
    return days_since_delivery <= RETURN_WINDOW_DAYS


def refund_amount(price: float, days_since_delivery: int) -> float:
    """Return the refund: full price within the window, 0.0 outside it."""
    if price < 0:
        raise ValueError("price must not be negative")
    if not within_return_window(days_since_delivery):
        return 0.0
    return round(price, 2)


def apply_promos(price: float, days_since_delivery: int, opened: bool = False) -> float:
    """Calculate refund amount with promotional adjustments.

    Args:
        price: Original item price
        days_since_delivery: Days since item was delivered
        opened: Whether the item has been opened (default: False for backward compatibility)

    Returns:
        Refund amount after applying policies. Opened items incur a 20% restocking fee.
    """
    base_refund = refund_amount(price, days_since_delivery)

    if base_refund == 0.0:
        return 0.0

    if opened:
        # Apply 20% restocking fee for opened items
        return round(base_refund * 0.8, 2)

    return base_refund


def expedited_refund(price: float, days_since_delivery: int, expedited: bool) -> float:
    """Calculate refund with expedited processing fee.

    Args:
        price: Original item price
        days_since_delivery: Days since delivery
        expedited: If True, add $10 expedited processing fee

    Returns:
        Refund amount with expedited fee added if applicable
    """
    if not isinstance(expedited, bool):
        raise ValueError("expedited must be a boolean")

    base = refund_amount(price, days_since_delivery)

    if expedited:
        return base + 10.0

    return base