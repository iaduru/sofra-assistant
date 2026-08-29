from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class Decision(str, Enum):
    ANSWERED = "answered"
    NEEDS_CONFIRMATION = "needs_confirmation"
    BLOCKED = "blocked"
    CLARIFY = "clarify"
    REFUSED = "refused"
    UNKNOWN = "unknown"

class GateRequirement(str, Enum):
    OUT_OF_SERVICE_AREA = "out_of_service_area"
    ITEM_UNAVAILABLE = "item_unavailable"
    AGE_18_PLUS = "age_18_plus"
    MIN_ORDER = "min_order"
    SUFFICIENT_FUNDS = "sufficient_funds"
    NOT_CANCELLABLE = "not_cancellable"
    TIP_WINDOW_EXPIRED = "tip_window_expired"

class AuditRecord(BaseModel):
    user_id: Optional[str] = None
    intent: Optional[str] = None
    tools_called: list[str] = Field(default_factory=list)
    decision: Decision
    reason: Optional[str] = None
    kb_doc_ids: list[str] = Field(default_factory=list)