import json
import sys

from sofra import config
from sofra.data.repository import Repository
from sofra.data.kb_retrieval import KBRetriever
from sofra.security.token import TokenStore
from sofra.conversation.state import ConversationManager
from sofra.agent.orchestrator import Orchestrator

AVAILABLE_USERS = ["u_ok", "u_unverified", "u_lowbalance", "u_new"]

def main() -> None:
    if not config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY is not defined in the .env file.", file=sys.stderr)
        sys.exit(1)

    print("Starting Sofra Assistant...")
    repo = Repository(
        users_path=config.USERS_PATH,
        restaurants_path=config.RESTAURANTS_PATH,
        carts_path=config.CARTS_PATH,
        orders_path=config.ORDERS_PATH,
    )
    kb = KBRetriever(config.KB_PATH)
    token_store = TokenStore()
    conversations = ConversationManager()
    orchestrator = Orchestrator(repo=repo, token_store=token_store, kb=kb)

    print(f"Ready. Available users: {', '.join(AVAILABLE_USERS)}\n")

    user_id = input(f"Select user_id ({'/'.join(AVAILABLE_USERS)}): ").strip() or "u_ok"
    if user_id not in AVAILABLE_USERS:
        print(f"Warning: '{user_id}' is not one of the predefined users, proceeding anyway.")

    conversation = conversations.get_or_create(user_id)

    while True:
        try:
            text = input(f"\n[{user_id}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not text:
            continue
        if text.lower() == "exit":
            break
        if text.lower() == "reset":
            conversations.reset(user_id)
            conversation = conversations.get_or_create(user_id)
            print("Conversation history has been reset.")
            continue

        result = orchestrator.handle_message(conversation, user_id, text)
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()