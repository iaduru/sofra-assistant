from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from sofra.config import TIP_WINDOW_DAYS
from sofra.models.audit import GateRequirement
from sofra.models.data_models import User, Restaurant, CartItem, CheckoutQuote, Order
from sofra.models.ui_blocks import VerificationGateBlock
from sofra.security.messages import GATE_ERROR_MESSAGES, DEFAULT_GATE_REASON, DEFAULT_GATE_CTA

class GateResult(BaseModel):
    passed: bool
    requirement: Optional[GateRequirement] = None
    reason: Optional[str] = None
    cta: Optional[str] = None

def to_verification_gate_block(result: GateResult) -> VerificationGateBlock:
    assert not result.passed and result.requirement is not None
    return VerificationGateBlock(
        requirement=result.requirement.value,
        reason=result.reason or DEFAULT_GATE_REASON,
        cta=result.cta or DEFAULT_GATE_CTA,
    )

class OrderContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    user: User
    restaurant: Restaurant
    items: list[CartItem]
    quote: CheckoutQuote

class Gate(ABC):
    @abstractmethod
    def check(self, ctx) -> Optional[GateResult]:
        ...

class ServiceAreaGate(Gate):
    def check(self, ctx: OrderContext) -> Optional[GateResult]:
        if not ctx.restaurant.delivers_to(ctx.user.district):
            msg = GATE_ERROR_MESSAGES[GateRequirement.OUT_OF_SERVICE_AREA]
            return GateResult(
                passed=False,
                requirement=GateRequirement.OUT_OF_SERVICE_AREA,
                reason=msg["reason"].format(
                    restaurant_name=ctx.restaurant.name, district=ctx.user.district
                ),
                cta=msg["cta"],
            )
        return None

class ItemAvailabilityGate(Gate):
    def check(self, ctx: OrderContext) -> Optional[GateResult]:
        for item in ctx.items:
            menu_item = ctx.restaurant.get_item(item.item_id)
            if menu_item is None or not menu_item.available:
                msg = GATE_ERROR_MESSAGES[GateRequirement.ITEM_UNAVAILABLE]
                return GateResult(
                    passed=False,
                    requirement=GateRequirement.ITEM_UNAVAILABLE,
                    reason=msg["reason"],
                    cta=msg["cta"],
                )
        return None

class AgeGate(Gate):
    def check(self, ctx: OrderContext) -> Optional[GateResult]:
        has_restricted = any(
            mi.age_restricted
            for i in ctx.items
            if (mi := ctx.restaurant.get_item(i.item_id)) is not None
        )
        if has_restricted and not ctx.user.age_verified:
            msg = GATE_ERROR_MESSAGES[GateRequirement.AGE_18_PLUS]
            return GateResult(
                passed=False,
                requirement=GateRequirement.AGE_18_PLUS,
                reason=msg["reason"],
                cta=msg["cta"],
            )
        return None

class MinOrderGate(Gate):
    def check(self, ctx: OrderContext) -> Optional[GateResult]:
        if not ctx.quote.meets_minimum:
            msg = GATE_ERROR_MESSAGES[GateRequirement.MIN_ORDER]
            return GateResult(
                passed=False,
                requirement=GateRequirement.MIN_ORDER,
                reason=msg["reason"].format(min_order=ctx.quote.min_order_try),
                cta=msg["cta"],
            )
        return None

class PaymentSufficiencyGate(Gate):
    def check(self, ctx: OrderContext) -> Optional[GateResult]:
        if ctx.user.wallet_balance_try < ctx.quote.total_try and not ctx.user.payment_method:
            msg = GATE_ERROR_MESSAGES[GateRequirement.SUFFICIENT_FUNDS]
            return GateResult(
                passed=False,
                requirement=GateRequirement.SUFFICIENT_FUNDS,
                reason=msg["reason"],
                cta=msg["cta"],
            )
        return None

PLACE_ORDER_GATES: list[Gate] = [
    ServiceAreaGate(),
    ItemAvailabilityGate(),
    AgeGate(),
    MinOrderGate(),
    PaymentSufficiencyGate(),
]

class CancelOrderContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    order: Order

class NotCancellableGate(Gate):
    def check(self, ctx: CancelOrderContext) -> Optional[GateResult]:
        if ctx.order.status != "received":
            msg = GATE_ERROR_MESSAGES[GateRequirement.NOT_CANCELLABLE]
            return GateResult(
                passed=False,
                requirement=GateRequirement.NOT_CANCELLABLE,
                reason=msg["reason"],
                cta=msg["cta"],
            )
        return None

CANCEL_ORDER_GATES: list[Gate] = [
    NotCancellableGate(),
]

class AddTipContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    order: Order
    user: User
    amount_try: float
    now: datetime

class TipWindowGate(Gate):
    def check(self, ctx: AddTipContext) -> Optional[GateResult]:
        if ctx.order.status == "cancelled":
            expired = True
        elif ctx.order.status == "delivered":
            delivered_date = datetime.fromisoformat(ctx.order.date)
            if ctx.now.tzinfo is not None and delivered_date.tzinfo is None:
                delivered_date = delivered_date.replace(tzinfo=ctx.now.tzinfo)

            expired = (ctx.now - delivered_date).days > TIP_WINDOW_DAYS
        else:
            expired = False
        if expired:
            msg = GATE_ERROR_MESSAGES[GateRequirement.TIP_WINDOW_EXPIRED]
            return GateResult(
                passed=False,
                requirement=GateRequirement.TIP_WINDOW_EXPIRED,
                reason=msg["reason"],
                cta=msg["cta"],
            )
        return None

class TipPaymentSufficiencyGate(Gate):
    def check(self, ctx: AddTipContext) -> Optional[GateResult]:
        if ctx.user.wallet_balance_try < ctx.amount_try and not ctx.user.payment_method:
            msg = GATE_ERROR_MESSAGES[GateRequirement.SUFFICIENT_FUNDS]
            return GateResult(
                passed=False,
                requirement=GateRequirement.SUFFICIENT_FUNDS,
                reason=msg["reason"],
                cta=msg["cta"],
            )
        return None

ADD_TIP_GATES: list[Gate] = [
    TipWindowGate(),
    TipPaymentSufficiencyGate(),
]

def run_gates(gates: list[Gate], ctx) -> Optional[GateResult]:
    for gate in gates:
        result = gate.check(ctx)
        if result is not None:
            return result
    return None