#!/usr/bin/env python3
"""Run synthetic order calculations with exact integer cents and yuan output."""

from smoke_demo.addition import add_cents, sum_values
from smoke_demo.format_cents import format_cents
from smoke_demo.order_subtotal import order_subtotal
from smoke_demo.shipping_fee import shipping_fee


def main() -> None:
    """Show paid shipping, free shipping, and exact large-amount formatting."""
    orders = (
        ("Standard shipping", [(199, 3), (250, 2)]),
        ("Free shipping", [(2500, 2)]),
    )
    for label, items in orders:
        subtotal = sum_values([
            order_subtotal(price_cents, quantity)
            for price_cents, quantity in items
        ])
        delivery = shipping_fee(subtotal, 500, 5000)
        total = add_cents(subtotal, delivery)
        print(label)
        print(f"  Subtotal: {format_cents(subtotal)} yuan")
        print(f"  Shipping: {format_cents(delivery)} yuan")
        print(f"  Total: {format_cents(total)} yuan")
    print(f"Large amount: {format_cents(9007199254740993)} yuan")


if __name__ == "__main__":
    main()
