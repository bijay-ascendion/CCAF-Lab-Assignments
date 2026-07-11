"""Order placement for NorthPeak."""

from __future__ import annotations

from decimal import Decimal

from auth.tokens import verify_token

CENTS = Decimal("0.01")


def count_items(items: list[dict]) -> int:
    """Return the number of items."""
    return len(items)


def place_order(token: str, items: list[dict]) -> dict:
    """Place an order if the caller's token is valid."""
    if not verify_token(token):
        raise PermissionError("invalid token")
    subtotal = sum((Decimal(str(i["price"])) for i in items), Decimal("0")).quantize(CENTS)
    return {"placed": True, "item_count": len(items), "subtotal": subtotal}
