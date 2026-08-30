from __future__ import annotations

class ConversationState:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.messages: list = []

class ConversationManager:
    def __init__(self) -> None:
        self._states: dict[str, ConversationState] = {}

    def get_or_create(self, user_id: str) -> ConversationState:
        if user_id not in self._states:
            self._states[user_id] = ConversationState(user_id)
        return self._states[user_id]

    def reset(self, user_id: str) -> None:
        self._states.pop(user_id, None)