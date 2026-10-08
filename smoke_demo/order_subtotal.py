"""Calculate an order subtotal using integer cents."""


def order_subtotal(unit_price_cents: int, quantity: int) -> int:
    """Return the subtotal in cents for a non-negative integer price and quantity.

    Raise TypeError for non-integers (including bool) and ValueError for
    negative integers. Both inputs are validated even when quantity is zero.
    """
    for name, value in (("unit_price_cents", unit_price_cents), ("quantity", quantity)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    return unit_price_cents * quantity
