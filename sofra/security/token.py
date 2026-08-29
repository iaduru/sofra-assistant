from __future__ import annotations
import hmac
import hashlib
import json
import base64
import uuid

from datetime import datetime, timedelta
from typing import Any, Optional
from sofra.config import CONFIRM_TOKEN_TTL_SECONDS, NOW, SECRET_KEY
from sofra.security.messages import TokenError

class TokenStore:
    def __init__(self, secret_key: bytes = SECRET_KEY) -> None:
        self._secret_key = secret_key
        self._used_nonces: set[str] = set()

    def generate(
        self,
        user_id: str,
        action: str,
        params: dict[str, Any],
        now: Optional[datetime] = None,
    ) -> tuple[str, str]:
        now = now or NOW
        nonce = str(uuid.uuid4())
        expires_at = now + timedelta(seconds=CONFIRM_TOKEN_TTL_SECONDS)
        expires_at_iso = expires_at.isoformat()

        payload_dict = {
            "user_id": user_id,
            "action": action,
            "params": params,
            "expires_at": expires_at_iso,
            "nonce": nonce,
        }
        payload_json = json.dumps(payload_dict, sort_keys=True)
        signature = hmac.new(
            self._secret_key, payload_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        encoded_payload = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8")
        token = f"{encoded_payload}.{signature}"
        return token, expires_at_iso

    def verify(
        self,
        token: str,
        expected_user_id: str,
        expected_action: str,
        expected_params: dict[str, Any],
        now: Optional[datetime] = None,
    ) -> tuple[bool, Optional[TokenError]]:
        now = now or NOW

        try:
            encoded_payload, signature = token.split(".")
            payload_json = base64.urlsafe_b64decode(encoded_payload).decode("utf-8")
            payload_dict = json.loads(payload_json)
        except Exception:
            return False, TokenError.MALFORMED

        expected_signature = hmac.new(
            self._secret_key, payload_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return False, TokenError.INVALID_SIGNATURE

        expires_at = datetime.fromisoformat(payload_dict["expires_at"])
        if now > expires_at:
            return False, TokenError.EXPIRED

        nonce = payload_dict["nonce"]
        if nonce in self._used_nonces:
            return False, TokenError.ALREADY_USED

        if (
            payload_dict["user_id"] != expected_user_id
            or payload_dict["action"] != expected_action
        ):
            return False, TokenError.MISMATCH

        if payload_dict["params"] != expected_params:
            return False, TokenError.PARAMS_CHANGED

        self._used_nonces.add(nonce)
        return True, None