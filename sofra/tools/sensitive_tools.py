from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from sofra.config import NOW, TIP_CAP_TRY
from sofra.data.repository import Repository
from sofra.models.audit import Decision
from sofra.models.data_models import CartItem, Order
from sofra.security.gates import (
    GateResult,
    OrderContext,
    CancelOrderContext,
    AddTipContext,
    PLACE_ORDER_GATES,
    CANCEL_ORDER_GATES,
    TipWindowGate,
    TipPaymentSufficiencyGate,
    run_gates,
)
from sofra.security.token import TokenStore
from sofra.security.messages import TokenError
from sofra.tools.messages import (
    TOOL_ERROR_USER_OR_REST_NOT_FOUND,
    TOOL_ERROR_ORDER_NOT_FOUND,
    TOOL_ERROR_ORDER_OR_USER_NOT_FOUND,
    TOOL_ERROR_INVALID_TIP_AMOUNT,
)
from sofra.tools.money import quote_checkout as _quote_checkout

class ActionOutcome(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    decision: Decision
    gate_result: Optional[GateResult] = None
    confirm_token: Optional[str] = None
    expires_at: Optional[str] = None
    order: Optional[Order] = None
    token_error: Optional[TokenError] = None
    error_message: Optional[str] = None

def _handle_invalid_token(err: TokenError) -> bool:
    return err != TokenError.MALFORMED

def place_order(
    repo: Repository,
    token_store: TokenStore,
    user_id: str,
    restaurant_id: str,
    items: list[dict],
    confirm_token: Optional[str] = None,
    now: Optional[datetime] = None,
) -> ActionOutcome:
    now = now or NOW
    user = repo.get_user(user_id)
    restaurant = repo.get_restaurant(restaurant_id)
    if user is None or restaurant is None:
        return ActionOutcome(decision=Decision.UNKNOWN, error_message=TOOL_ERROR_USER_OR_REST_NOT_FOUND)

    cart_items = [CartItem(**i) for i in items]
    quote = _quote_checkout(restaurant, cart_items)
    ctx = OrderContext(user=user, restaurant=restaurant, items=cart_items, quote=quote)

    gate_result = run_gates(PLACE_ORDER_GATES, ctx)
    if gate_result is not None:
        return ActionOutcome(decision=Decision.BLOCKED, gate_result=gate_result)

    params = {"restaurant_id": restaurant_id, "items": [i.model_dump() for i in cart_items]}

    if confirm_token is None:
        token, expires_at = token_store.generate(user_id, "place_order", params, now=now)
        return ActionOutcome(decision=Decision.NEEDS_CONFIRMATION, confirm_token=token, expires_at=expires_at)

    ok, err = token_store.verify(confirm_token, user_id, "place_order", params, now=now)
    if not ok:
        if _handle_invalid_token(err):
            new_token, new_expires = token_store.generate(user_id, "place_order", params, now=now)
            return ActionOutcome(
                decision=Decision.NEEDS_CONFIRMATION,
                confirm_token=new_token, expires_at=new_expires, token_error=err,
            )
        return ActionOutcome(decision=Decision.REFUSED, token_error=err)

    order = repo.create_order(
        user_id=user_id, restaurant_name=restaurant.name,
        total_try=quote.total_try, date=now.date().isoformat(),
    )
    return ActionOutcome(decision=Decision.ANSWERED, order=order)

def cancel_order(
    repo: Repository,
    token_store: TokenStore,
    user_id: str,
    order_id: str,
    confirm_token: Optional[str] = None,
    now: Optional[datetime] = None,
) -> ActionOutcome:
    now = now or NOW
    order = repo.get_order(user_id, order_id)
    if order is None:
        return ActionOutcome(decision=Decision.UNKNOWN, error_message=TOOL_ERROR_ORDER_NOT_FOUND)

    ctx = CancelOrderContext(order=order)
    gate_result = run_gates(CANCEL_ORDER_GATES, ctx)
    if gate_result is not None:
        return ActionOutcome(decision=Decision.BLOCKED, gate_result=gate_result)

    params = {"order_id": order_id}

    if confirm_token is None:
        token, expires_at = token_store.generate(user_id, "cancel_order", params, now=now)
        return ActionOutcome(decision=Decision.NEEDS_CONFIRMATION, confirm_token=token, expires_at=expires_at)

    ok, err = token_store.verify(confirm_token, user_id, "cancel_order", params, now=now)
    if not ok:
        if _handle_invalid_token(err):
            new_token, new_expires = token_store.generate(user_id, "cancel_order", params, now=now)
            return ActionOutcome(
                decision=Decision.NEEDS_CONFIRMATION,
                confirm_token=new_token, expires_at=new_expires, token_error=err,
            )
        return ActionOutcome(decision=Decision.REFUSED, token_error=err)

    updated_order = repo.cancel_order(user_id, order_id)
    return ActionOutcome(decision=Decision.ANSWERED, order=updated_order)

def add_tip(
    repo: Repository,
    token_store: TokenStore,
    user_id: str,
    order_id: str,
    amount_try: float,
    confirm_token: Optional[str] = None,
    now: Optional[datetime] = None,
) -> ActionOutcome:
    now = now or NOW
    order = repo.get_order(user_id, order_id)
    user = repo.get_user(user_id)
    if order is None or user is None:
        return ActionOutcome(decision=Decision.UNKNOWN, error_message=TOOL_ERROR_ORDER_OR_USER_NOT_FOUND)

    window_ctx = AddTipContext(order=order, user=user, amount_try=amount_try, now=now)
    window_result = TipWindowGate().check(window_ctx)
    if window_result is not None:
        return ActionOutcome(decision=Decision.BLOCKED, gate_result=window_result)

    cap = min(order.total_try, TIP_CAP_TRY)
    if amount_try <= 0 or amount_try > cap:
        return ActionOutcome(
            decision=Decision.CLARIFY,
            error_message=TOOL_ERROR_INVALID_TIP_AMOUNT.format(cap=cap),
        )

    payment_result = TipPaymentSufficiencyGate().check(window_ctx)
    if payment_result is not None:
        return ActionOutcome(decision=Decision.BLOCKED, gate_result=payment_result)

    params = {"order_id": order_id, "amount_try": amount_try}

    if confirm_token is None:
        token, expires_at = token_store.generate(user_id, "add_tip", params, now=now)
        return ActionOutcome(decision=Decision.NEEDS_CONFIRMATION, confirm_token=token, expires_at=expires_at)

    ok, err = token_store.verify(confirm_token, user_id, "add_tip", params, now=now)
    if not ok:
        if _handle_invalid_token(err):
            new_token, new_expires = token_store.generate(user_id, "add_tip", params, now=now)
            return ActionOutcome(
                decision=Decision.NEEDS_CONFIRMATION,
                confirm_token=new_token, expires_at=new_expires, token_error=err,
            )
        return ActionOutcome(decision=Decision.REFUSED, token_error=err)

    updated_order = repo.add_tip(user_id, order_id, amount_try)
    return ActionOutcome(decision=Decision.ANSWERED, order=updated_order)