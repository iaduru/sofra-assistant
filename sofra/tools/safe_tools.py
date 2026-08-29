from __future__ import annotations
from typing import Optional
from sofra.data.repository import Repository
from sofra.models.data_models import CartItem
from sofra.tools.money import quote_checkout as _quote_checkout

def get_user(repo: Repository, user_id: str) -> Optional[dict]:
    user = repo.get_user(user_id)
    return user.model_dump() if user else None

def get_cart(repo: Repository, user_id: str) -> Optional[dict]:
    cart = repo.get_cart(user_id)
    return cart.model_dump() if cart else None

def search_restaurants(
    repo: Repository,
    q: Optional[str] = None,
    cuisine: Optional[str] = None,
    near_district: Optional[str] = None,
) -> list[dict]:
    results = repo.search_restaurants(q=q, cuisine=cuisine, near_district=near_district)
    return [
        {
            "id": r.id,
            "name": r.name,
            "cuisine": r.cuisine,
            "rating": r.rating,
            "district": r.district,
            "delivery_fee_try": r.delivery_fee_try,
            "min_order_try": r.min_order_try,
            "eta_min": r.eta_min,
        }
        for r in results
    ]

def get_menu(repo: Repository, restaurant_id: str) -> Optional[list[dict]]:
    restaurant = repo.get_restaurant(restaurant_id)
    if restaurant is None:
        return None
    return [item.model_dump() for item in restaurant.menu]

def quote_checkout(
    repo: Repository, restaurant_id: str, items: list[dict]
) -> Optional[dict]:
    restaurant = repo.get_restaurant(restaurant_id)
    if restaurant is None:
        return None
    cart_items = [CartItem(**i) for i in items]
    quote = _quote_checkout(restaurant, cart_items)
    return quote.model_dump()

def list_orders(repo: Repository, user_id: str) -> list[dict]:
    return [order.model_dump() for order in repo.list_orders(user_id)]