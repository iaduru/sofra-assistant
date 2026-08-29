from enum import Enum
from sofra.models.audit import GateRequirement

DEFAULT_GATE_REASON = "Action blocked by security gate."
DEFAULT_GATE_CTA = "Review details"

class TokenError(str, Enum):
    MALFORMED = "malformed_token"
    INVALID_SIGNATURE = "invalid_signature"
    EXPIRED = "token_expired"
    ALREADY_USED = "token_already_used"
    MISMATCH = "action_or_user_mismatch"
    PARAMS_CHANGED = "parameters_changed"


TOKEN_ERROR_MESSAGES = {
    TokenError.MALFORMED: "The provided confirmation token is malformed.",
    TokenError.INVALID_SIGNATURE: "The confirmation token signature is invalid.",
    TokenError.EXPIRED: "The confirmation token has expired.",
    TokenError.ALREADY_USED: "This confirmation token has already been used.",
    TokenError.MISMATCH: "The action or user does not match the token.",
    TokenError.PARAMS_CHANGED: "The transaction parameters have changed since the token was issued.",
}

GATE_ERROR_MESSAGES = {
    GateRequirement.OUT_OF_SERVICE_AREA: {
        "reason": "{restaurant_name} does not deliver to {district}.",
        "cta": "Change address or select another restaurant",
    },
    GateRequirement.ITEM_UNAVAILABLE: {
        "reason": "An item in your cart is no longer available.",
        "cta": "Review cart",
    },
    GateRequirement.AGE_18_PLUS: {
        "reason": "Your cart contains age-restricted items, but your age is not verified.",
        "cta": "Verify Age",
    },
    GateRequirement.MIN_ORDER: {
        "reason": "The minimum order value is {min_order} TL (excluding delivery).",
        "cta": "Add more items",
    },
    GateRequirement.SUFFICIENT_FUNDS: {
        "reason": "Your wallet balance is insufficient and no card is saved.",
        "cta": "Top up wallet or add a card",
    },
    GateRequirement.NOT_CANCELLABLE: {
        "reason": "This order can no longer be cancelled (already past the 'received' stage).",
        "cta": "Contact support",
    },
    GateRequirement.TIP_WINDOW_EXPIRED: {
        "reason": "The tipping window for this order has closed.",
        "cta": "View order history",
    },
}