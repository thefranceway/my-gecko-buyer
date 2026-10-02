from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from solders.pubkey import Pubkey

from . import letmebuy

if TYPE_CHECKING:
    from .intent import IntentRecord
    from .prepared import Prepared


class NotYetWritten(NotImplementedError):
    def __init__(self, what: str, hint: str) -> None:
        self.what, self.hint = what, hint
        super().__init__(f"{what} is not written yet ({hint})")


@dataclass(frozen=True)
class FieldResult:
    field: str
    ok: bool
    asked: Any
    found: Any
    where: str = "prepared"
    note: str = ""

    def line(self) -> str:
        if self.ok:
            return f"{self.field}: {self.found!r}"
        text = f"{self.field}: asked {self.asked!r}, {self.where} {self.found!r}"
        return f"{text} ({self.note})" if self.note else text


class Refused(Exception):
    def __init__(self, result: FieldResult) -> None:
        self.result = result
        super().__init__(result.line())


def refuse(
    field_name: str, asked: Any, found: Any, where: str = "prepared", note: str = ""
) -> FieldResult:
    return FieldResult(field_name, False, asked, found, where, note)


def agree(field_name: str, value: Any) -> FieldResult:
    return FieldResult(field_name, True, value, value)


def check_program(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    expected = str(letmebuy.program_id())
    if prepared.program != expected:
        return refuse("program", expected, prepared.program)
    if prepared.programs != (expected,):
        return refuse(
            "program", [expected], list(prepared.programs), note="an extra program is called"
        )
    return agree("program", expected)


def check_store(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    expected = str(letmebuy.store_address(intent.store))
    if prepared.store != expected:
        return refuse("store", f"{intent.store} at {expected}", prepared.store)
    return agree("store", expected)


def check_product(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    if prepared.product != intent.product:
        return refuse("product", intent.product, prepared.product)
    return agree("product", intent.product)


def check_price(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    if prepared.price_raw is None:
        return refuse("price_raw", intent.budget_raw, None, note="no amount reported")
    if prepared.price_raw > intent.budget_raw:
        return refuse("price_raw", intent.budget_raw, prepared.price_raw)
    return agree("price_raw", prepared.price_raw)


def check_mint(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    if prepared.mint != intent.mint:
        return refuse("mint", intent.mint, prepared.mint)
    return agree("mint", intent.mint)


def check_quantity(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    if prepared.quantity != intent.quantity:
        return refuse("quantity", intent.quantity, prepared.quantity)
    return agree("quantity", intent.quantity)


def check_destination(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    expected = str(
        letmebuy.token_account(
            Pubkey.from_string(intent.store_authority), Pubkey.from_string(intent.mint)
        )
    )
    if prepared.destination != expected:
        return refuse("destination", expected, prepared.destination)
    return agree("destination", expected)


CHECKS: tuple[Callable[[IntentRecord, Prepared], FieldResult], ...] = (
    check_program,
    check_store,
    check_product,
    check_price,
    check_mint,
    check_quantity,
    check_destination,
)


@dataclass
class Verdict:
    results: list[FieldResult] = field(default_factory=list)
    refusal: FieldResult | None = None
    unwritten: NotYetWritten | None = None

    @property
    def passed(self) -> bool:
        return self.refusal is None and self.unwritten is None


def check_all(intent: IntentRecord, prepared: Prepared) -> Verdict:
    verdict = Verdict()
    for check in CHECKS:
        try:
            result = check(intent, prepared)
        except NotYetWritten as todo:
            verdict.unwritten = todo
            return verdict
        verdict.results.append(result)
        if not result.ok:
            verdict.refusal = result
            return verdict
    return verdict
