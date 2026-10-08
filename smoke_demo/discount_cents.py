"""Deduct a discount from an amount using exact integer cents."""


def discount_cents(amount_cents: int, discount_cents: int) -> int:
    """Return the amount after a discount, with a minimum result of zero.

    Raise TypeError for non-integers (including bool) and ValueError for
    negative integers. Both inputs are validated even when the result is zero.
    """
    for name, value in (("amount_cents", amount_cents), ("discount_cents", discount_cents)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    return max(0, amount_cents - discount_cents)
