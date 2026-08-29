from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field

class User(BaseModel):
    id: str
    display_name: str
    wallet_balance_try: float
    payment_method: bool
    age_verified: bool
    address: str
    district: str

class MenuItem(BaseModel):
    item_id: str
    name: str
    price_try: float
    category: str
    age_restricted: bool = False
    available: bool = True

class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: str
    city: str
    rating: float
    delivery_fee_try: float
    min_order_try: float
    eta_min: int
    district: str
    delivery_districts: list[str]
    menu: list[MenuItem] = Field(default_factory=list)

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        return next((i for i in self.menu if i.item_id == item_id), None)

    def delivers_to(self, district: str) -> bool:
        return district in self.delivery_districts

class CartItem(BaseModel):
    item_id: str
    qty: int

class Cart(BaseModel):
    user_id: str
    restaurant_id: Optional[str] = None
    items: list[CartItem] = Field(default_factory=list)

OrderStatus = Literal["received", "delivered", "cancelled"]

class Order(BaseModel):
    order_id: str
    user_id: str
    date: str
    restaurant: str
    total_try: float
    status: OrderStatus
    note: str = ""
    tip_try: float = 0.0

class CheckoutQuote(BaseModel):
    subtotal_try: float
    delivery_fee_try: float
    total_try: float
    min_order_try: float
    meets_minimum: bool
    free_delivery_threshold_try: float