# Disposable workflow smoke test

This repository contains synthetic, disposable test fixtures for checking a
branch / pull-request / continuous-integration workflow. These examples are not
business requirements, a production application, or a deployment target.

The baseline contains an import smoke test. Task A adds integer addition and its
tests. Task B independently adds integer subtraction and its tests. Both tasks
start from the same baseline so their integration can be tested separately.

Run the standard-library-only test suite with Python 3.12:

```sh
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs this command for pull requests targeting
`develop` and pushes to `develop`. It has read-only repository permissions,
does not persist checkout credentials, and has no production or deployment step.
No application secrets or third-party Python packages are needed.

## Order subtotal fixture

`smoke_demo.order_subtotal.order_subtotal(unit_price_cents, quantity)` returns
an exact integer subtotal in cents. For example, `order_subtotal(199, 3)` returns
`597`, and a zero quantity returns `0`. Both arguments must be non-negative
integers: negative values raise `ValueError`, while non-integers (including
booleans) raise `TypeError`. Invalid prices are still rejected when quantity is
zero. The function uses only Python's standard library.

## Shipping fee fixture

`smoke_demo.shipping_fee.shipping_fee(cart_subtotal_cents, base_fee_cents,
free_shipping_threshold_cents)` returns the base fee below the threshold and
`0` at or above it. For example, `shipping_fee(4999, 500, 5000)` returns `500`,
while `shipping_fee(5000, 500, 5000)` returns `0`. All amounts are integer cents.
All three arguments must be non-negative integers: negative values raise
`ValueError`, and non-integers (including booleans) raise `TypeError`, even when
shipping would otherwise be free. A zero threshold makes shipping free.
