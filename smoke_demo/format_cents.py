"""Format non-negative integer cents as exact yuan strings."""


def format_cents(amount_cents: int) -> str:
    """Return a yuan string with exactly two decimal places, without floats.

    Raise TypeError for non-integers (including bool) and ValueError for
    negative integers.
    """
    if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
        raise TypeError("amount_cents must be an integer")
    if amount_cents < 0:
        raise ValueError("amount_cents must be non-negative")
    yuan, cents = divmod(amount_cents, 100)
    # Small decimal chunks avoid Python's limit on converting huge integers.
    groups = []
    while yuan >= 1_000_000_000:
        yuan, group = divmod(yuan, 1_000_000_000)
        groups.append(f"{group:09d}")
    whole_yuan = str(yuan) + "".join(reversed(groups))
    return f"{whole_yuan}.{cents:02d}"
