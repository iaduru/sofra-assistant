from __future__ import annotations
import json
from typing import Optional
from sofra.models.data_models import User, Restaurant, Cart, Order

class Repository:
    def __init__(
        self,
        users_path: str,
        restaurants_path: str,
        carts_path: str,
        orders_path: str,
    ) -> None:
        self._users: dict[str, User] = self._load_users(users_path)
        self._restaurants: dict[str, Restaurant] = self._load_restaurants(restaurants_path)
        self._carts: dict[str, Cart] = self._load_carts(carts_path)
        self._orders: dict[str, list[Order]] = self._load_orders(orders_path)
        self._order_counter: dict[str, int] = {
            user_id: len(orders) for user_id, orders in self._orders.items()
        }

    @staticmethod
    def _load_users(path: str) -> dict[str, User]:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return {u["id"]: User(**u) for u in raw["users"]}

    @staticmethod
    def _load_restaurants(path: str) -> dict[str, Restaurant]:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return {r["id"]: Restaurant(**r) for r in raw["restaurants"]}

    @staticmethod
    def _load_carts(path: str) -> dict[str, Cart]:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return {user_id: Cart(user_id=user_id, **c) for user_id, c in raw.items()}

    @staticmethod
    def _load_orders(path: str) -> dict[str, list[Order]]:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        return {
            user_id: [Order(user_id=user_id, **o) for o in olist]
            for user_id, olist in raw.items()
        }

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_restaurant(self, restaurant_id: str) -> Optional[Restaurant]:
        return self._restaurants.get(restaurant_id)

    def search_restaurants(
        self,
        q: Optional[str] = None,
        cuisine: Optional[str] = None,
        near_district: Optional[str] = None,
    ) -> list[Restaurant]:
        results = list(self._restaurants.values())
        if near_district:
            results = [r for r in results if r.delivers_to(near_district)]
        if cuisine:
            results = [r for r in results if r.cuisine.lower() == cuisine.lower()]
        if q:
            q_lower = q.lower()
            results = [
                r for r in results
                if q_lower in r.name.lower() or any(q_lower in mi.name.lower() for mi in r.menu)
            ]
        return results

    def get_cart(self, user_id: str) -> Optional[Cart]:
        return self._carts.get(user_id)

    def list_orders(self, user_id: str) -> list[Order]:
        return self._orders.get(user_id, [])

    def get_order(self, user_id: str, order_id: str) -> Optional[Order]:
        for order in self.list_orders(user_id):
            if order.order_id == order_id:
                return order
        return None

    def create_order(
        self, user_id: str, restaurant_name: str, total_try: float, date: str
    ) -> Order:
        self._order_counter[user_id] = self._order_counter.get(user_id, 0) + 1
        order_id = f"{user_id}_new_{self._order_counter[user_id]}"
        order = Order(
            order_id=order_id,
            user_id=user_id,
            date=date,
            restaurant=restaurant_name,
            total_try=total_try,
            status="received",
            note="",
        )
        self._orders.setdefault(user_id, []).append(order)
        return order

    def cancel_order(self, user_id: str, order_id: str) -> Optional[Order]:
        order = self.get_order(user_id, order_id)
        if order is None:
            return None
        order.status = "cancelled"
        return order

    def add_tip(self, user_id: str, order_id: str, amount_try: float) -> Optional[Order]:
        order = self.get_order(user_id, order_id)
        if order is None:
            return None
        order.tip_try += amount_try
        return order

def load_repository_from_config() -> Repository:
    from sofra import config
    return Repository(
        users_path=config.USERS_PATH,
        restaurants_path=config.RESTAURANTS_PATH,
        carts_path=config.CARTS_PATH,
        orders_path=config.ORDERS_PATH,
    )