"""Synthetic addition fixture, not production application logic."""


def add(left: int, right: int) -> int:
    """Return the sum of two integer operands."""
    return left + right


def add_cents(left: int, right: int) -> int:
    """Return the exact sum of two non-negative integer amounts in cents.

    Raise TypeError for non-integers (including bool) and ValueError for
    negative integers.
    """
    for name, value in (("left", left), ("right", right)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be an integer")
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    return left + right
