# my-gecko-buyer — a buyer that pays, or says why not

I open my own store on Solana devnet and my buyer pins intent, checks 7 fields, signs only after simulation, and writes one receipt read from ledger.

**Landed devnet:** https://explorer.solana.com/tx/5qMqaX1GLRVWKWnzpDWXnME8MQAg2awg7LW1V8FkEUcXU3SyCH3uq8Fy7WwpkkhRR16Jr92KmtxUsgXiRdMa67J1?cluster=devnet
Store `dev3multiuniverse` — `total_purchases` 0 -> 1 — slot 506672200

---

## What I built

Buyer agent for Gecko (Solana) that enforces **refusals before signing**. If a check fails, nothing is signed.

Flow in `buyer/agent.py`:
1. `pin` intent to `intents/<timestamp>.json` BEFORE prepare
2. `prepare` via Gecko MCP
3. 7 checks in `buyer/check.py` — compare `asked` vs `prepared`
4. if any fails → write `refusals/<case>.json` naming field + both values, no signature
5. if all pass → sign, verify, submit, write `receipts/<sig>.md` with 2 ledger reads

7 checks:
- mint, price_raw, quantity, budget, store address, product name, stale (40s sim)

5 cases + trap (`fixtures/cases/`):
- quantity, budget, mint, price, stale + trap that must NOT refuse

4 judge cards (`refusals/`):
- quantity asks 2 prepared 1
- budget asks half price
- tampered mint/price
- stale simulation

## Receipt — `receipts/5qMqaX1G.md`

**one espresso**, from `dev3multiuniverse` on devnet: reconciled with the ledger.

- signature: 5qMqaX1GLRVWKWnzpDWXnME8MQAg2awg7LW1V8FkEUcXU3SyCH3uq8Fy7WwpkkhRR16Jr92KmtxUsgXiRdMa67J1
- explorer: https://explorer.solana.com/tx/5qMqaX1GLRVWKWnzpDWXnME8MQAg2awg7LW1V8FkEUcXU3SyCH3uq8Fy7WwpkkhRR16Jr92KmtxUsgXiRdMa67J1?cluster=devnet
- slot: 506672200
- product: Espresso
- price_raw: 1000000 — mint HGEiGcGjQGwcVT5g1hUdMVgavAjPRhhfKDPzB86FdhDh
- buyer delta: -1000000 / store delta: +1000000
- total_purchases: 0 to 1
- intent pinned at: 2026-10-02T14:51:21.440967+00:00
- source: devnet

## Refusal — `refusals/`

Example (replace with your newest `refusals/*.json`):

```json
{
  "card": "quantity",
  "field": "quantity",
  "asked": 2,
  "prepared": 1,
  "refusal": "asked 2 espressos, prepared 1 — quantity mismatch"
}
```
Every refusal is written BEFORE signing and names the field.

## How to run

```bash
uv run buyer --cases --recorded     # 5 cases + trap offline — 6/6
uv run buyer --cards --recorded     # 4 judge cards offline
uv run buyer "one espresso" --devnet  # live buy from my store
GECKO_SOURCE=recorded uv run buyer "one espresso" --devnet  # fallback if devnet down
uv run pytest -q -o addopts='' --color=no  # 98 passed, 2 skipped
```

## Repo map for defence (which folder to open)

- `README.md` — this file, sentence + explorer link
- `store/store.json` — my store address
- `buyer/mcp_client.py` — Gecko hosted MCP call list_stores
- `buyer/agent.py` + `buyer/check.py` + `buyer/intent.py` — the loop + checks
- `intents/` — pins with timestamp before prepare
- `receipts/` — signatures + ledger reads, buyer delta = -price, store delta = +price
- `refusals/` — 4+ JSON naming field and both values
- `tests/` + `fixtures/cases/` — unit + integration, offline
- `docs/adr/0001-refusals-before-signing.md` — decision: refuse BEFORE signing
- `docs/DEFENCE.md` + `docs/ISSUES.md` — 6-min script + error codes
- `scripts/mainnet_wallet.py` + `scripts/devnet_setup.py` — wallet show
- `.github/workflows/check.yml` — CI: ruff, mypy, pytest — All checks passed!
- `.githooks/` — key scan, demo/ deleted

## Safety

- No key in repo — key in ~/.config/dev3pack/, genesis hash check
- Budget cap 300000 lamports for mainnet, devnet only for defence
- Intent pinned before prepare, so receipt can be traced back
- Key scan: 0 files

## Status

Branch main up to date with origin/main — 823b98c — Everything up-to-date — working tree clean
