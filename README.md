# Integer-cent helpers and local quote previews

This repository contains exact integer-cent helpers, a runnable amount example,
and a local HTTP quote preview service. Everything uses Python's standard library;
there are no third-party dependencies or external services.

The repository began as disposable branch / pull-request / continuous-integration
fixtures. The original arithmetic examples remain covered by regression tests.
The quote service previews totals locally; it does not place orders or deploy a
production application.

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

## Deducting discounts in cents

`smoke_demo.discount_cents.discount_cents(amount_cents, discount_cents)` deducts
a discount from an amount in exact integer cents. The result is `0` when the
discount equals or exceeds the amount:

```python
from smoke_demo.discount_cents import discount_cents

discount_cents(1999, 500)  # 1499 cents
discount_cents(500, 500)   # 0 cents
discount_cents(500, 700)   # 0 cents
discount_cents(1999, 0)    # 1999 cents
discount_cents(0, 500)     # 0 cents
discount_cents(9007199254740993, 2)  # 9007199254740991 cents, exactly
```

Both arguments must be non-negative integers. Negative integers raise
`ValueError`; non-integers, including booleans, raise `TypeError`. Both inputs
are validated even when the result would be zero. Integer arithmetic preserves
large amounts without floating-point conversion or rounding.

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

## Local HTTP quote previews

The existing cent helpers also power a stateless, loopback-only quote preview
service. It uses Python 3.12's standard library, needs no installation or external
service, and does not create orders, store customer data, or log requests.

From the repository root:

```sh
python -B quote_server.py --port 8001
```

The server binds only `127.0.0.1`. Port `8001` is the default; `--port 0` lets the
OS choose an available port. The first stdout line is the actual URL, for example
`http://127.0.0.1:43127`. Use that printed port in requests. An occupied port causes
a clear error and nonzero exit; the service never stops an existing listener or
silently picks another port. Keep any existing service on port `8000` untouched.
An absolute path to `quote_server.py` also works from another directory.

Stop a foreground server with Ctrl+C. On POSIX, SIGTERM to the specific process
also closes its listener and exits successfully. Do not use broad process-killing
commands. This local preview service has no authentication or TLS and is not a
public-facing production HTTP server.

### Requests and responses

`GET /health` returns status `200` and `{"status":"ok"}`.

`POST /quote` accepts a UTF-8 JSON object, with `Content-Length` supplied by your
HTTP client. Example using the default port:

```sh
curl --max-time 5 http://127.0.0.1:8001/quote \
  -H 'Content-Type: application/json' \
  --data '{"items":[{"unit_price_cents":199,"quantity":3},{"unit_price_cents":250,"quantity":2}],"shipping_fee_cents":500,"free_shipping_threshold_cents":5000}'
```

Response (`200`):

```json
{"subtotal_cents":1097,"shipping_cents":500,"total_cents":1597,"formatted_total":"15.97"}
```

- `items` must contain at least one object. Every item needs `unit_price_cents`
  and `quantity`.
- The top-level `shipping_fee_cents` and `free_shipping_threshold_cents` fields
  are required. They represent the base shipping fee and the free-shipping
  threshold, respectively.
- All four numeric input fields must be non-negative JSON integers. Booleans,
  decimals such as `1.0`, strings, nulls, and negative values are rejected.
  Zero quantities, zero prices, and zero shipping fees are valid.
- The existing `order_subtotal`, `shipping_fee`, and `format_cents` functions
  provide the calculation. Shipping is free when the subtotal reaches or exceeds
  the threshold; a zero threshold always gives free shipping. Every supplied
  numeric field is validated even when its result would otherwise be zero.
- Responses preserve exact integer cents, including amounts beyond JavaScript's
  safe-integer range. `formatted_total` is a yuan string with two decimal places,
  without a currency symbol. Clients must use an integer-safe JSON parser if
  they consume very large numeric fields.
- Extra fields are ignored. Duplicate JSON keys, nonstandard constants such as
  `NaN`, malformed JSON, missing fields, and invalid values return `400` with a
  JSON `error` string. Request bodies must be 1–65,536 bytes; chunked transfer and
  missing/duplicate/invalid `Content-Length` headers are rejected with `400`.
- Unknown paths return `404`; unsupported methods on these two paths return
  `405`. Paths match exactly, without trailing slashes or query strings.
- Responses include `Cache-Control: no-store`. Connections close after each
  response, with a five-second socket inactivity timeout. A slow connection
  does not block other requests. No request bodies, paths, or client addresses
  are written to logs or application storage.

Run the complete regression suite, including real HTTP requests and process
lifecycle checks:

```sh
python -B -m unittest discover -s tests -v
```

The new tests use OS-assigned loopback ports, bounded request/process timeouts,
and cleanup scoped to subprocesses they created. They do not use port `8000`.
