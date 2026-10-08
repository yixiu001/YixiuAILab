"""Synthetic division fixture, not production application logic."""


def divide(a, b):
    """Return a / b, raising ValueError when the divisor is zero."""
    if b == 0:
        raise ValueError("divisor must not be zero")
    return a / b
