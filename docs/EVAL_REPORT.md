# Evaluation report

## The five cases and the trap

| # | Ask | Expected | Recorded | Devnet | Evidence |
|---|---|---|---|---|---|
| 1 | one espresso | lands, receipt reconciles | MATCH | MATCH | `4yc7jA8LA...` |
| 2 | one general-admission ticket | refuse on `product` | MATCH | — | `refusals/...` |
| 3 | module 3, paid in USDC | refuse on `mint` | MATCH | — | `refusals/...` |
| 4 | tip up to 2 USDC | refuse on `price_raw` | MATCH | — | `refusals/...` |
| 5 | two bags of beans | refuse on `quantity` | MATCH | — | `refusals/...` |
| trap | one latte | refuse, name quoted back | MATCH | — | `refusals/...` |

Command: `uv run buyer --cases --recorded` gave **6/6**.

The recorded espresso purchase was submitted on devnet and reconciled successfully:
buyer `-1000000`, store `+1000000`, `total_purchases 0 to 1`.

## The four Friday cards

| Card | Expected | Result | Command |
|---|---|---|---|
| quantity | refuse on `quantity` | MATCH | `uv run buyer "two espressos" --devnet` |
| budget | refuse on `price_raw` | MATCH | `uv run buyer "one espresso" --budget-raw 500000 --devnet` |
| tampered bytes | verify refuses, nothing submitted | MATCH | `uv run buyer --card tampered` |
| stale bytes | signer refuses, prepare again | MATCH | `uv run buyer --card stale` |

Command: `uv run buyer --cards --recorded` gave **4/4**.

## Tests

`uv run pytest -q -o addopts='' --color=no`: **98 passed, 2 skipped**.

All tests completed successfully with no failures.

## Receipts reconciled with the ledger

The recorded espresso purchase produced devnet transaction:

`4yc7jA8LAjpZc3FXyMBbaeYqJMRQmr5Dmwmhj5Nos7ZrmTzuhftMa76UR6M3UwMLVLXWMXpaXAhhorMieUoXBZzf`

The receipt reconciled with the ledger:

- buyer delta: `-1000000`
- store delta: `+1000000`
- `total_purchases`: `0 -> 1`

The transaction landed on devnet at slot `505358840`.

The other five recorded cases intentionally refused before signing, so there were no receipts to reconcile.

## What this does not prove

- The evidence is based on Solana devnet and recorded fixtures, not mainnet.
- The evaluation covers the specific products, prices, quantities, mints, and failure cases represented by these fixtures.
- The checks verify the prepared transaction against the pinned expectations; they do not establish that an incorrect external pin could never be signed if the pin itself were wrong.
- A successful devnet transaction does not establish production readiness or mainnet reliability.
