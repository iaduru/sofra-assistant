from __future__ import annotations
from sofra.config import FREE_DELIVERY_THRESHOLD_TRY
from sofra.models.data_models import Restaurant, CartItem, User, CheckoutQuote

def quote_checkout(restaurant: Restaurant, items: list[CartItem]) -> CheckoutQuote:

    subtotal_try = 0.0
    for cart_item in items:
        menu_item = restaurant.get_item(cart_item.item_id)
        if menu_item is None:
            raise ValueError(
                f"item_id={cart_item.item_id!r} is not present in the menu of restaurant "
                f"(restaurant_id={restaurant.id!r}). This condition should have been intercepted "
                f"by the ItemAvailabilityGate prior to reaching quote_checkout."
            )
        subtotal_try += menu_item.price_try * cart_item.qty

    meets_minimum = subtotal_try >= restaurant.min_order_try

    if subtotal_try >= FREE_DELIVERY_THRESHOLD_TRY:
        delivery_fee_try = 0.0
    else:
        delivery_fee_try = restaurant.delivery_fee_try

    total_try = subtotal_try + delivery_fee_try

    return CheckoutQuote(
        subtotal_try=subtotal_try,
        delivery_fee_try=delivery_fee_try,
        total_try=total_try,
        min_order_try=restaurant.min_order_try,
        meets_minimum=meets_minimum,
        free_delivery_threshold_try=FREE_DELIVERY_THRESHOLD_TRY,
    )

def is_payment_sufficient(user: User, total_try: float) -> bool:
    if user.wallet_balance_try >= total_try:
        return True
    return user.payment_method