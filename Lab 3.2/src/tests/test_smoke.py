from decimal import Decimal
import pytest

from auth.tokens import verify_token
from orders.service import place_order, count_items
from payments.charges import charge

GOOD = "npk_live_abcdef123456"


def test_verify_token():
    assert verify_token(GOOD) is True
    assert verify_token("short") is False


def test_place_order():
    out = place_order(GOOD, [{"name": "Tent", "price": 289.0}])
    assert out["placed"] and out["item_count"] == 1


def test_place_order_subtotal_is_exact_decimal():
    out = place_order(GOOD, [{"price": "0.1"}, {"price": "0.2"}])
    assert out["subtotal"] == Decimal("0.30")


def test_charge():
    out = charge(GOOD, "50.00")
    assert out["charged"] is True
    assert out["amount"] == Decimal("50.00")


def test_count_items():
    items = [{"name": "Tent"}, {"name": "Sleeping bag"}, {"name": "Backpack"}]
    assert count_items(items) == 3
    assert count_items([]) == 0


def test_charge_exceeds_limit():
    """Test that amounts over $10,000 are rejected."""
    with pytest.raises(ValueError, match="exceeds the \\$10,000 limit"):
        charge(GOOD, "10000.01")
    with pytest.raises(ValueError, match="exceeds the \\$10,000 limit"):
        charge(GOOD, 50_000)
