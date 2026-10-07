"""Intentional fault injection for a disposable negative CI test; do not merge."""


def subtract(left: int, right: int) -> int:
    """Return the difference of two integer operands."""
    return left + right  # Intentional fault injection.
