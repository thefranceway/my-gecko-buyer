# my-gecko-buyer — a buyer that pays, or says why not

I open my own store on Solana devnet and my buyer pins intent, checks 7 fields, signs only after simulation, and writes one receipt read from ledger.

**Landed devnet:** https://explorer.solana.[STRIPPED 95 bytes]?cluster=devnet
Store `dev3multiuniverse` — `total_purchases` 0 -> 1 — slot 506672200

---

## What I built

Buyer agent for Gecko that enforces **refusals before signing**.

Flow in `buyer/agent.py`: pin -> prepare -> 7 checks -> sign -> verify -> submit
7 checks: mint, price_raw, quantity, budget, store address, product name, stale

## Receipt — `receipts/5qMqaX1G.md`

- signature: [STRIPPED 89 bytes] slot: 506672200
- product: Espresso price_raw 1000000 mint HGEiGcGjQGwcVT5g1hUdMVgavAjPRhhfKDPzB86FdhDh
- buyer delta -1000000 / store delta +1000000 / total_purchases 0 to 1

## Refusal — `refusals/`

Every refusal is written BEFORE signing and names the field. Example `quantity`: asked 2 prepared 1

## How to run

uv run buyer --cases --recorded
uv run buyer --cards --recorded
uv run buyer "one espresso" --devnet
uv run pytest -q -o addopts='' --color=no
