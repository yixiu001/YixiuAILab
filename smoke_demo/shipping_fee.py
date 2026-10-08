"""Calculate a shipping fee using integer cents."""


def shipping_fee(
    cart_subtotal_cents: int,
    base_fee_cents: int,
    free_shipping_threshold_cents: int,
) -> int:
    """Return zero at or above the free-shipping threshold, else the base fee.

    Raise TypeError for non-integers (including bool) and ValueError for
    negative integers. All inputs are validated even when shipping is free.
    """
    for name, value in (
        ("cart_subtotal_cents", cart_subtotal_cents),
        ("base_fee_cents", base_fee_cents),
        ("free_shipping_threshold_cents", free_shipping_threshold_cents),
    ):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    if cart_subtotal_cents >= free_shipping_threshold_cents:
        return 0
    return base_fee_cents
