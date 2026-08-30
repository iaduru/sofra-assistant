import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

NOW: datetime = datetime(2026, 8, 20, 12, 0, 0, tzinfo=timezone.utc)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCHEMA_DIR = os.path.join(BASE_DIR, "schema")

USERS_PATH = os.path.join(DATA_DIR, "users.json")
RESTAURANTS_PATH = os.path.join(DATA_DIR, "restaurants.json")
CARTS_PATH = os.path.join(DATA_DIR, "carts.json")
ORDERS_PATH = os.path.join(DATA_DIR, "orders.json")
KB_PATH = os.path.join(DATA_DIR, "knowledge", "kb.jsonl")
UI_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "ui_spec.schema.json")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_secret_str = os.getenv("SECRET_KEY", "secret-hmac-key")
SECRET_KEY: bytes = _secret_str.encode("utf-8")

CONFIRM_TOKEN_TTL_SECONDS = 5 * 60
TIP_CAP_TRY = 500
TIP_WINDOW_DAYS = 7
FREE_DELIVERY_THRESHOLD_TRY = 250
