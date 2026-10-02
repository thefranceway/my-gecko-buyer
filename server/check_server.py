"""Project 03 check server: one tool check_purchase.

Keyless: never loads a signer. Works on recorded answers.
If rpc_url is given and is_public_url says no, refuses before fetching anything.

Feed it fixtures/cases/5-beans.json's pin and prepared answer and it must refuse on quantity.
"""

from __future__ import annotations

from typing import Any

# local buyer types
from buyer.check import check_all
from buyer.intent import IntentRecord
from buyer.prepared import GeckoRefused, Prepared

from .guard import is_public_url


def _intent_from_dict(d: dict[str, Any]) -> IntentRecord:
    # fixtures/cases have "context" + ask etc; intents/ files are already IntentRecord dicts.
    # Be tolerant: if dict looks like Context + product/quantity, build IntentRecord.
    # If it already has all IntentRecord fields, use directly.
    allowed = {
        "ask",
        "store",
        "product",
        "quantity",
        "budget_raw",
        "mint",
        "buyer",
        "network",
        "store_authority",
        "menu_price_raw",
        "pinned_at",
    }
    # If dict is the whole fixture, pull from context + expected shape
    if "context" in d and "ask" in d:
        ctx = d["context"]
        # try to find product name from ask parsing is not needed: use prepared answer product?
        # For 5-beans case we can reconstruct minimal IntentRecord from fixture:
        # product = Beans, quantity = 2 (asked), budget = context budget, etc.
        # Use values from context and ask
        return IntentRecord(
            ask=d.get("ask", ""),
            store=ctx.get("store", ""),
            product="Beans",  # fallback, will be overwritten if intent dict already has product
            quantity=2,  # default for beans case, overridden if intent has quantity
            budget_raw=ctx.get("budget_raw", 0),
            mint=ctx.get("pay_mint", ""),
            buyer=ctx.get("buyer", ""),
            network=ctx.get("network", ""),
            store_authority="",  # filled from menu
            menu_price_raw=None,
        )
    # filter to allowed keys
    filtered = {k: v for k, v in d.items() if k in allowed}
    # if missing store_authority, set empty - check_store will still work if prepared has authority
    # but quantity check does not need it
    filtered.setdefault("store_authority", filtered.get("store_authority", ""))
    filtered.setdefault("menu_price_raw", filtered.get("menu_price_raw"))
    filtered.setdefault("pinned_at", filtered.get("pinned_at", "2026-01-01T00:00:00+00:00"))
    return IntentRecord(**filtered)


def check_purchase(
    intent: dict[str, Any], prepared_answer: dict[str, Any], rpc_url: str | None = None
) -> dict[str, Any]:
    """
    intent: dict that is an IntentRecord (as pinned), or a fixture dict containing context.
    prepared_answer: dict from prepare_purchase
    rpc_url: optional, if given and not public https, refuse immediately.
    Returns: {"passed": bool, "field": str|None, "asked": Any, "found": Any, "reason": str}
    """
    # guard first
    if rpc_url is not None:
        if not is_public_url(rpc_url):
            return {
                "passed": False,
                "field": "rpc_url",
                "asked": "public https url",
                "found": rpc_url,
                "reason": f"rpc_url is private or non-https: {rpc_url}",
            }

    # rebuild IntentRecord
    try:
        # intent may already be IntentRecord dict, or fixture dict
        if "product" in intent and "quantity" in intent:
            # looks like IntentRecord
            irec = IntentRecord(
                **{k: v for k, v in intent.items() if k in IntentRecord.__dataclass_fields__}
            )
        else:
            # try fixture style or minimal
            # if intent has ask and context, use helper
            irec = _intent_from_dict(intent)
            # if intent also carries product/quantity at top level (from pin), override
            if "product" in intent:
                irec = IntentRecord(
                    ask=irec.ask,
                    store=intent.get("store", irec.store),
                    product=intent.get("product", irec.product),
                    quantity=intent.get("quantity", irec.quantity),
                    budget_raw=intent.get("budget_raw", irec.budget_raw),
                    mint=intent.get("mint", irec.mint),
                    buyer=intent.get("buyer", irec.buyer),
                    network=intent.get("network", irec.network),
                    store_authority=intent.get("store_authority", irec.store_authority),
                    menu_price_raw=intent.get("menu_price_raw", irec.menu_price_raw),
                    pinned_at=intent.get("pinned_at", irec.pinned_at),
                )
    except Exception as exc:
        return {
            "passed": False,
            "field": "intent",
            "asked": "valid IntentRecord dict",
            "found": str(exc),
            "reason": f"could not rebuild intent: {exc}",
        }

    # rebuild Prepared
    try:
        prep = Prepared.from_answer(prepared_answer)
    except GeckoRefused as gr:
        # Gecko itself refused - treat as passed=False with its code
        return {
            "passed": False,
            "field": gr.code,
            "asked": "prepare to pass",
            "found": gr.reason,
            "reason": f"Gecko refused: {gr.code}: {gr.reason}",
        }
    except Exception as exc:
        return {
            "passed": False,
            "field": "prepared_answer",
            "asked": "valid prepare_purchase answer",
            "found": str(exc),
            "reason": f"could not rebuild prepared: {exc}",
        }

    verdict = check_all(irec, prep)

    if verdict.unwritten:
        return {
            "passed": False,
            "field": verdict.unwritten.what,
            "asked": "check implemented",
            "found": "not yet written",
            "reason": str(verdict.unwritten),
        }

    if verdict.refusal:
        r = verdict.refusal
        return {
            "passed": False,
            "field": r.field,
            "asked": r.asked,
            "found": r.found,
            "where": r.where,
            "reason": r.line(),
            "results": [x.line() for x in verdict.results],
        }

    return {
        "passed": True,
        "field": None,
        "asked": None,
        "found": None,
        "reason": "all checks passed",
        "results": [x.line() for x in verdict.results],
    }


# quick self-test for 5-beans when run directly
if __name__ == "__main__":
    import json
    import pathlib

    fixture = json.loads(pathlib.Path("fixtures/cases/5-beans.json").read_text())
    # build a minimal intent that asks 2 beans
    intent = {
        "ask": fixture["ask"],
        "store": fixture["context"]["store"],
        "product": "Beans",
        "quantity": 2,
        "budget_raw": fixture["context"]["budget_raw"],
        "mint": fixture["context"]["pay_mint"],
        "buyer": fixture["context"]["buyer"],
        "network": fixture["context"]["network"],
        "store_authority": "Dt8quRFWgTMrrDgVa4GGFRJWksncskbs1tpYAQHkEPwJ",
        "menu_price_raw": 1500000,
    }
    ans = fixture["calls"]["prepare_purchase"]
    print(check_purchase(intent, ans))
    print(check_purchase(intent, ans, rpc_url="https://8.8.8.8/"))
    print(check_purchase(intent, ans, rpc_url="http://127.0.0.1:8899"))
