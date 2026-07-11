import pytest

from northpeak.refunds import within_return_window, refund_amount, apply_promos, expedited_refund


def test_within_window_boundary():
    assert within_return_window(0) is True
    assert within_return_window(30) is True
    assert within_return_window(31) is False


def test_full_refund_within_window():
    assert refund_amount(100.0, 10) == 100.0


def test_full_refund_at_window_edge():
    # Day 30 is the last day inside the 30-day window: still a full refund.
    assert refund_amount(100.0, 30) == 100.0


def test_no_refund_after_window():
    assert refund_amount(100.0, 45) == 0.0


def test_no_refund_just_outside_window():
    # Day 31 is the first day outside the window: refund is 0.
    assert refund_amount(100.0, 31) == 0.0


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        refund_amount(-1.0, 5)
    with pytest.raises(ValueError):
        within_return_window(-1)


def test_apply_promos_opened_true_applies_restocking_fee():
    """When opened=True, a 20% restocking fee is deducted from the refund."""
    # $100 item within window, opened -> $80 refund (20% fee)
    assert apply_promos(100.0, 10, opened=True) == 80.0


def test_apply_promos_opened_false_no_restocking_fee():
    """When opened=False, no restocking fee is applied."""
    # $100 item within window, not opened -> $100 refund
    assert apply_promos(100.0, 10, opened=False) == 100.0


def test_apply_promos_default_no_restocking_fee():
    """When opened is omitted (default), no restocking fee is applied (backward compatible)."""
    # $100 item within window, opened not specified -> $100 refund
    assert apply_promos(100.0, 10) == 100.0


def test_apply_promos_outside_window_returns_zero():
    """Items outside the return window get no refund regardless of opened status."""
    assert apply_promos(100.0, 31, opened=True) == 0.0
    assert apply_promos(100.0, 31, opened=False) == 0.0
    assert apply_promos(100.0, 45) == 0.0


def test_expedited_refund_adds_processing_fee():
    """When expedited=True, add $10 expedited processing fee to base refund."""
    # $100 item within window, expedited -> $110 refund
    assert expedited_refund(100.0, 10, expedited=True) == 110.0


def test_expedited_refund_no_fee_when_false():
    """When expedited=False, no processing fee is added."""
    # $100 item within window, not expedited -> $100 refund
    assert expedited_refund(100.0, 10, expedited=False) == 100.0


def test_expedited_refund_outside_window():
    """Expedited processing doesn't apply outside the return window."""
    # Outside window -> $0 base refund, expedited still adds $10
    assert expedited_refund(100.0, 31, expedited=True) == 10.0
    assert expedited_refund(100.0, 31, expedited=False) == 0.0


def test_expedited_refund_validates_expedited_parameter():
    """The expedited parameter must be a boolean."""
    with pytest.raises(ValueError, match="expedited must be a boolean"):
        expedited_refund(100.0, 10, expedited="yes")
    with pytest.raises(ValueError, match="expedited must be a boolean"):
        expedited_refund(100.0, 10, expedited=1)
