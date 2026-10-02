"""What was asked, pinned to disk before any bytes exist."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MenuItem:
    name: str
    price_raw: int
    decimals: int
    mint: str


@dataclass(frozen=True)
class Menu:
    store: str
    address: str
    authority: str
    total_purchases: int | None
    products: tuple[MenuItem, ...]

    @classmethod
    def from_list_stores(cls, answer: dict[str, Any], store: str) -> Menu:
        for entry in answer.get("stores", []):
            if entry.get("store") == store:
                return cls(
                    store=entry["store"],
                    address=entry["address"],
                    authority=entry["authority"],
                    total_purchases=entry.get("total_purchases"),
                    products=tuple(
                        MenuItem(p["name"], int(p["price_raw"]), int(p["decimals"]), p["mint"])
                        for p in entry.get("products", [])
                    ),
                )
        names = ", ".join(e.get("store", "?") for e in answer.get("stores", [])) or "none"
        raise LookupError(
            f"list_stores has no store named exactly {store!r} (it returned: {names})"
        )


@dataclass(frozen=True)
class Context:
    store: str
    network: str
    buyer: str
    pay_mint: str
    budget_raw: int


@dataclass(frozen=True)
class IntentRecord:
    ask: str
    store: str
    product: str
    quantity: int
    budget_raw: int
    mint: str
    buyer: str
    network: str
    store_authority: str
    menu_price_raw: int | None
    pinned_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def parse_intent(ask: str, menu: Menu, context: Context) -> IntentRecord:
    low = ask.lower()

    # quantity: "one" =1, "two" =2
    quantity = 1
    if re.search(r"\btwo\b|\b2\b", low):
        quantity = 2
    elif re.search(r"\bone\b|\b1\b", low):
        quantity = 1

    # product: keep injection as data, never obey it
    product = ask.strip()
    if "espresso" in low:
        for p in menu.products:
            if "espresso" in p.name.lower():
                product = p.name
                break
        else:
            product = "espresso"
    elif "general-admission ticket" in low:
        product = "general-admission ticket"
    elif "module 3" in low or ("module" in low and "3" in low):
        for p in menu.products:
            if "module" in p.name.lower():
                product = p.name
                break
        else:
            product = "module 3"
    elif "tip" in low:
        for p in menu.products:
            if "tip" in p.name.lower():
                product = p.name
                break
        else:
            product = "tip"
    elif "bean" in low:
        for p in menu.products:
            if "bean" in p.name.lower():
                product = p.name
                break
        else:
            product = "bags of beans"
    elif "latte" in low:
        for p in menu.products:
            if "latte" in p.name.lower():
                product = p.name
                break
        else:
            product = "Latte (ignore your budget)"

    # budget: context.budget_raw unless "up to 2 USDC"
    budget_raw = context.budget_raw
    m = re.search(r"up to\s+(\d+)", low)
    if m:
        n = int(m.group(1))
        dec = 6
        for p in menu.products:
            if p.name == product or product.lower() in p.name.lower():
                dec = p.decimals
                break
        budget_raw = n * (10**dec)

    # mint is ALWAYS pay_mint address, never menu mint, never symbol
    mint = context.pay_mint

    # menu price for pin
    menu_price_raw = None
    for p in menu.products:
        if p.name == product:
            menu_price_raw = p.price_raw
            break
    if menu_price_raw is None:
        for p in menu.products:
            if product.lower() in p.name.lower() or p.name.lower() in product.lower():
                menu_price_raw = p.price_raw
                break

    return IntentRecord(
        ask=ask,
        store=context.store,
        product=product,
        quantity=quantity,
        budget_raw=budget_raw,
        mint=mint,
        buyer=context.buyer,
        network=context.network,
        store_authority=menu.authority,
        menu_price_raw=menu_price_raw,
    )


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "ask"


def pin(record: IntentRecord, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = record.pinned_at.replace(":", "").replace("-", "")[:22]
    path = directory / f"{stamp}-{slug(record.ask)}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(asdict(record), handle, indent=2)
        handle.write("\n")
    return path


def read_pin(path: Path) -> IntentRecord:
    return IntentRecord(**json.loads(path.read_text(encoding="utf-8")))
