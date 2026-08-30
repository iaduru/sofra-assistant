from __future__ import annotations
import json

from google import genai
from google.genai import types
from sofra.config import GEMINI_API_KEY, GEMINI_MODEL
from sofra.data.repository import Repository
from sofra.data.kb_retrieval import KBRetriever
from sofra.security.token import TokenStore
from sofra.conversation.state import ConversationState
from sofra.agent.tool_specs import TOOL_SPECS
from sofra.agent.system_prompt import SYSTEM_PROMPT
from sofra.agent.constants import (
    ERR_USER_NOT_FOUND,
    ERR_CART_NOT_FOUND,
    ERR_RESTAURANT_NOT_FOUND,
    MSG_MAX_ROUNDS,
    MSG_NO_TEXT,
    MSG_SCHEMA_FAILED,
)
from sofra.tools import safe_tools, sensitive_tools
from sofra.models.ui_blocks import UIResponse, ErrorBlock
from sofra.models.audit import AuditRecord, Decision

_MAX_TOOL_ROUNDS = 8

class Orchestrator:
    def __init__(
        self,
        repo: Repository,
        token_store: TokenStore,
        kb: KBRetriever,
        api_key: str = GEMINI_API_KEY,
        model: str = GEMINI_MODEL,
    ) -> None:
        self._repo = repo
        self._token_store = token_store
        self._kb = kb
        self._client = genai.Client(api_key=api_key)
        self._model = model

        self._tool_registry = {
            "get_user": lambda i: safe_tools.get_user(self._repo, **i) or {"error": ERR_USER_NOT_FOUND},
            "get_cart": lambda i: safe_tools.get_cart(self._repo, **i) or {"error": ERR_CART_NOT_FOUND},
            "search_restaurants": lambda i: {"results": safe_tools.search_restaurants(self._repo, **i)},
            "get_menu": lambda i: self._handle_get_menu(i),
            "quote_checkout": lambda i: safe_tools.quote_checkout(self._repo, **i) or {"error": ERR_RESTAURANT_NOT_FOUND},
            "list_orders": lambda i: {"orders": safe_tools.list_orders(self._repo, **i)},
            "search_knowledge_base": lambda i: {"results": self._kb.search(i["query"], top_k=i.get("top_k", 5))},
            "place_order": lambda i: sensitive_tools.place_order(self._repo, self._token_store, **i).model_dump(mode="json"),
            "cancel_order": lambda i: sensitive_tools.cancel_order(self._repo, self._token_store, **i).model_dump(mode="json"),
            "add_tip": lambda i: sensitive_tools.add_tip(self._repo, self._token_store, **i).model_dump(mode="json"),
        }

        function_declarations = [
            types.FunctionDeclaration(
                name=spec["name"],
                description=spec["description"],
                parameters_json_schema=spec["input_schema"],
            )
            for spec in TOOL_SPECS
        ]
        self._tool = types.Tool(function_declarations=function_declarations)
        self._generate_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[self._tool],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

    def _handle_get_menu(self, tool_input: dict) -> dict:
        result = safe_tools.get_menu(self._repo, **tool_input)
        return {"menu": result} if result is not None else {"error": ERR_RESTAURANT_NOT_FOUND}

    def _dispatch_tool(self, name: str, tool_input: dict) -> dict:
        try:
            handler = self._tool_registry.get(name)
            if not handler:
                return {"error": f"unknown_tool:{name}"}
            return handler(tool_input)
        except Exception as e:
            return {"error": f"tool_execution_failed: {e}"}

    def handle_message(self, conversation: ConversationState, user_id: str, user_text: str) -> dict:
        tagged_text = f"[user_id: {user_id}]\n{user_text}"
        conversation.messages.append(
            types.Content(role="user", parts=[types.Part.from_text(text=tagged_text)])
        )

        for _ in range(_MAX_TOOL_ROUNDS):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=conversation.messages,
                    config=self._generate_config,
                )
            except Exception as e:
                return self._fallback_error(f"Gemini API temporarily unavailable: {e}")

            candidate = response.candidates[0] if response.candidates else None
            if candidate is None or candidate.content is None:
                return self._fallback_error(MSG_NO_TEXT)

            conversation.messages.append(candidate.content)

            function_call_parts = [
                part for part in (candidate.content.parts or []) if part.function_call is not None
            ]

            if not function_call_parts:
                break

            response_parts = []
            for part in function_call_parts:
                fc = part.function_call
                result = self._dispatch_tool(fc.name, dict(fc.args or {}))
                response_parts.append(
                    types.Part.from_function_response(name=fc.name, response=result)
                )

            conversation.messages.append(types.Content(role="user", parts=response_parts))
        else:
            return self._fallback_error(MSG_MAX_ROUNDS)

        final_text = "".join(
            part.text for part in (candidate.content.parts or []) if part.text
        )
        if not final_text:
            return self._fallback_error(MSG_NO_TEXT)

        clean_text = final_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            parsed = json.loads(clean_text)
            validated = UIResponse.model_validate(parsed)
        except Exception as e:
            return self._fallback_error(MSG_SCHEMA_FAILED.format(e))

        return validated.model_dump(mode="json")

    @staticmethod
    def _fallback_error(message: str) -> dict:
        fallback = UIResponse(
            blocks=[ErrorBlock(code="invalid_response", message=message)],
            audit=AuditRecord(decision=Decision.UNKNOWN),
        )
        return fallback.model_dump(mode="json")