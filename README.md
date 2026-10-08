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

## Integer list sum fixture

`smoke_demo.addition.sum_values(values)` sums a list of integers, including
negative values. An empty list returns `0`. Booleans and non-integer elements
raise `TypeError`; the input list is left unchanged.

```python
from smoke_demo.addition import sum_values

sum_values([2, -3, 5])  # 4
sum_values([])  # 0
sum_values([1, True])  # raises TypeError
```

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

## Adding amounts in cents

`smoke_demo.addition.add_cents(left, right)` adds two non-negative integer
amounts in cents without rounding:

```python
from smoke_demo.addition import add_cents

add_cents(199, 250)  # 449 cents
add_cents(0, 199)    # 199 cents
```

Negative integers raise `ValueError`. Non-integers, including booleans, raise
`TypeError` in either argument. The existing `add(left, right)` function keeps
its original behavior.

## Cents formatting fixture

`smoke_demo.format_cents.format_cents(amount_cents)` converts integer cents to
a yuan string with exactly two decimal places. For example, `format_cents(0)`
returns `"0.00"`, `format_cents(1)` returns `"0.01"`, and `format_cents(12345)`
returns `"123.45"`. The input must be a non-negative integer: negative integers
raise `ValueError`, and non-integers (including booleans) raise `TypeError`.
Integer division and remainder preserve precision for large amounts without
using floating-point arithmetic; `format_cents(9007199254740993)` returns
`"90071992547409.93"` exactly. No currency symbol or grouping separator is added.
Decimal output is assembled in small chunks, so even amounts exceeding Python's
default integer-to-string digit limit work without changing global settings.

## Project flow illustration

![Project flow illustration showing three connected stages](docs/images/project-flow.png)

The illustration accompanies the example's flow: calculate integer-cent
subtotals, add shipping, and format the resulting amounts as yuan strings.

## Runnable amount example

From the repository root, run the standard-library-only example with Python 3.12:

```sh
python money_demo.py
```

On POSIX systems with `python3` available, the script is also directly executable:

```sh
./money_demo.py
```

The example combines `order_subtotal`, `sum_values`, `shipping_fee`, `add_cents`,
and `format_cents`. It shows an order below the free-shipping threshold, one
exactly at the threshold, and a large amount formatted without precision loss.
These remain synthetic examples; all calculations use integer cents.

Expected output:

```text
Standard shipping
  Subtotal: 10.97 yuan
  Shipping: 5.00 yuan
  Total: 15.97 yuan
Free shipping
  Subtotal: 50.00 yuan
  Shipping: 0.00 yuan
  Total: 50.00 yuan
Large amount: 90071992547409.93 yuan
```

The existing unittest command also checks both execution methods, execution
from another working directory, and importing the example without output.
