from __future__ import annotations
from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from sofra.models.audit import AuditRecord

class _StrictBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

class TextBlock(_StrictBlock):
    type: Literal["text"] = "text"
    markdown: str

class RestaurantCardBlock(_StrictBlock):
    type: Literal["restaurant_card"] = "restaurant_card"
    restaurant_id: str
    name: str
    cuisine: Optional[str] = None
    rating: Optional[float] = None
    delivery_fee_try: Optional[float] = None
    min_order_try: Optional[float] = None
    eta_min: Optional[int] = None
    district: Optional[str] = None

class MenuItemBlock(_StrictBlock):
    type: Literal["menu_item"] = "menu_item"
    item_id: str
    name: str
    price_try: float
    available: bool
    age_restricted: bool
    category: Optional[str] = None

class CartSummaryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    qty: int
    price_try: float

class CartSummaryBlock(_StrictBlock):
    type: Literal["cart_summary"] = "cart_summary"
    items: list[CartSummaryItem]
    total_try: float
    restaurant_id: Optional[str] = None
    subtotal_try: Optional[float] = None
    delivery_fee_try: Optional[float] = None
    min_order_try: Optional[float] = None
    meets_minimum: Optional[bool] = None

class OrderSummaryBlock(_StrictBlock):
    type: Literal["order_summary"] = "order_summary"
    order_id: str
    status: str
    restaurant: Optional[str] = None
    total_try: Optional[float] = None
    eta_min: Optional[int] = None

class ConfirmationPromptBlock(_StrictBlock):
    type: Literal["confirmation_prompt"] = "confirmation_prompt"
    action: Literal["place_order", "cancel_order", "add_tip"]
    summary: str
    params: dict[str, Any]
    confirm_token: str
    expires_at: str

class VerificationGateBlock(_StrictBlock):
    type: Literal["verification_gate"] = "verification_gate"
    requirement: Literal[
        "out_of_service_area",
        "item_unavailable",
        "age_18_plus",
        "min_order",
        "sufficient_funds",
        "not_cancellable",
        "tip_window_expired",
    ]
    reason: str
    cta: str

class SuggestedActionsBlock(_StrictBlock):
    type: Literal["suggested_actions"] = "suggested_actions"
    chips: list[str]

class ErrorBlock(_StrictBlock):
    type: Literal["error"] = "error"
    code: str
    message: str

Block = Union[
    TextBlock,
    RestaurantCardBlock,
    MenuItemBlock,
    CartSummaryBlock,
    OrderSummaryBlock,
    ConfirmationPromptBlock,
    VerificationGateBlock,
    SuggestedActionsBlock,
    ErrorBlock,
]

class UIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["1"] = "1"
    blocks: list[Block] = Field(..., min_length=1, discriminator="type")
    audit: AuditRecord