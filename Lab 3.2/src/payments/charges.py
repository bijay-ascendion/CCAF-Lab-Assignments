"""Payment charges for NorthPeak."""

from __future__ import annotations

from decimal import Decimal

from auth.tokens import verify_token

CENTS = Decimal("0.01")


def charge(token: str, amount: Decimal | float | str) -> dict:
    """Charge an amount if the caller's token is valid."""
    if not verify_token(token):
        raise PermissionError("invalid token")
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("amount must be positive")
    if amount > 10_000:
        raise ValueError("amount exceeds the $10,000 limit")
    return {"charged": True, "amount": amount.quantize(CENTS)}
