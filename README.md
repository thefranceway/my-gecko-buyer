# my-gecko-buyer — a buyer that pays, or says why not

I open my own store on Solana devnet and my buyer pins intent, checks 7 fields, signs only after simulation, and writes one receipt read from ledger.

**Landed devnet:** https://explorer.solana.com/tx/5qMqaX1GLRVWKWnzpDWXnME8MQAg2awg7LW1V8FkEUcXU3SyCH3uq8Fy7WwpkkhRR16Jr92KmtxUsgXiRdMa67J1?cluster=devnet
Store `dev3multiuniverse` — total_purchases 0 -> 1 — slot 506672200

## Receipt — receipts/5qMqaX1G.md

**one espresso**, from `dev3multiuniverse` on devnet: reconciled with the ledger.
- signature: 5qMqaX1GLRVWKWnzpDWXnME8MQAg2awg7LW1V8FkEUcXU3SyCH3uq8Fy7WwpkkhRR16Jr92KmtxUsgXiRdMa67J1
- slot: 506672200
- product: Espresso
- price_raw: 1000000 — mint HGEiGcGjQGwcVT5g1hUdMVgavAjPRhhfKDPzB86FdhDh
- buyer delta: -1000000 / store delta: +1000000
- total_purchases: 0 to 1
- intent pinned at: 2026-10-02T14:51:21.440967+00:00

## Refusal — refusals/

Run `uv run buyer --cards --recorded` to generate 4 refusals. Each names field and both values before signing.

## How to run

uv run buyer --cases --recorded
uv run buyer --cards --recorded
uv run buyer "one espresso" --devnet
uv run pytest -q -o addopts='' --color=no

## What I built

buyer/agent.py: pin -> prepare -> 7 checks -> sign -> verify -> submit
buyer/check.py: mint, price_raw, quantity, budget, store address, product name, stale
fixtures/cases/: 5 cases + trap
refusals/: 4 cards written BEFORE signing
receipts/: ledger proof
