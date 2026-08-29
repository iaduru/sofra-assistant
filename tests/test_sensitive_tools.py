import pytest
from datetime import timedelta
from sofra import config
from sofra.data.repository import Repository
from sofra.security.token import TokenStore
from sofra.security.messages import TokenError
from sofra.models.audit import Decision, GateRequirement
from sofra.tools import sensitive_tools as st

@pytest.fixture
def repo():
    return Repository(
        users_path=config.USERS_PATH,
        restaurants_path=config.RESTAURANTS_PATH,
        carts_path=config.CARTS_PATH,
        orders_path=config.ORDERS_PATH,
    )

@pytest.fixture
def token_store():
    return TokenStore()

def test_prompt_4_place_order_confirm_flow(repo, token_store):
    items = [{"item_id": "itm_013", "qty": 2}]

    outcome1 = st.place_order(repo, token_store, "u_ok", "rst_04", items, confirm_token=None)
    assert outcome1.decision == Decision.NEEDS_CONFIRMATION
    assert outcome1.confirm_token is not None
    orders_before = len(repo.list_orders("u_ok"))

    outcome2 = st.place_order(
        repo, token_store, "u_ok", "rst_04", items, confirm_token=outcome1.confirm_token
    )
    assert outcome2.decision == Decision.ANSWERED
    assert outcome2.order is not None
    assert len(repo.list_orders("u_ok")) == orders_before + 1

def test_prompt_14_reused_token_no_double_order(repo, token_store):
    items = [{"item_id": "itm_013", "qty": 2}]
    outcome1 = st.place_order(repo, token_store, "u_ok", "rst_04", items, confirm_token=None)
    outcome2 = st.place_order(
        repo, token_store, "u_ok", "rst_04", items, confirm_token=outcome1.confirm_token
    )
    assert outcome2.decision == Decision.ANSWERED
    orders_after_first = len(repo.list_orders("u_ok"))

    outcome3 = st.place_order(
        repo, token_store, "u_ok", "rst_04", items, confirm_token=outcome1.confirm_token
    )
    assert outcome3.decision == Decision.NEEDS_CONFIRMATION
    assert outcome3.token_error == TokenError.ALREADY_USED
    assert len(repo.list_orders("u_ok")) == orders_after_first

def test_prompt_16_changed_params_rejects_old_token(repo, token_store):
    items_2 = [{"item_id": "itm_013", "qty": 2}]
    items_5 = [{"item_id": "itm_013", "qty": 5}]

    outcome1 = st.place_order(repo, token_store, "u_ok", "rst_04", items_2, confirm_token=None)
    orders_before = len(repo.list_orders("u_ok"))

    outcome2 = st.place_order(
        repo, token_store, "u_ok", "rst_04", items_5, confirm_token=outcome1.confirm_token
    )
    assert outcome2.decision == Decision.NEEDS_CONFIRMATION
    assert outcome2.token_error == TokenError.PARAMS_CHANGED
    assert len(repo.list_orders("u_ok")) == orders_before

def test_prompt_17_expired_token(repo, token_store):
    items = [{"item_id": "itm_013", "qty": 2}]
    future = config.NOW + timedelta(minutes=6)

    outcome1 = st.place_order(repo, token_store, "u_ok", "rst_04", items, confirm_token=None, now=config.NOW)
    orders_before = len(repo.list_orders("u_ok"))

    outcome2 = st.place_order(
        repo, token_store, "u_ok", "rst_04", items,
        confirm_token=outcome1.confirm_token, now=future,
    )
    assert outcome2.decision == Decision.NEEDS_CONFIRMATION
    assert outcome2.token_error == TokenError.EXPIRED
    assert len(repo.list_orders("u_ok")) == orders_before

def test_prompt_18_cancel_order_flow(repo, token_store):
    outcome1 = st.cancel_order(repo, token_store, "u_ok", "u_ok_o9", confirm_token=None)
    assert outcome1.decision == Decision.NEEDS_CONFIRMATION

    order_before = repo.get_order("u_ok", "u_ok_o9")
    assert order_before.status == "received"

    outcome2 = st.cancel_order(
        repo, token_store, "u_ok", "u_ok_o9", confirm_token=outcome1.confirm_token
    )
    assert outcome2.decision == Decision.ANSWERED
    assert outcome2.order.status == "cancelled"

def test_prompt_19_cancel_delivered_order_not_cancellable(repo, token_store):
    outcome = st.cancel_order(repo, token_store, "u_ok", "u_ok_o1", confirm_token=None)
    assert outcome.decision == Decision.BLOCKED
    assert outcome.gate_result.requirement == GateRequirement.NOT_CANCELLABLE
    assert repo.get_order("u_ok", "u_ok_o1").status == "delivered"

def test_prompt_20_tip_window_expired(repo, token_store):
    outcome = st.add_tip(repo, token_store, "u_ok", "u_ok_o1", 50.0, confirm_token=None, now=config.NOW)
    assert outcome.decision == Decision.BLOCKED
    assert outcome.gate_result.requirement == GateRequirement.TIP_WINDOW_EXPIRED

def test_prompt_5_low_balance_no_card(repo, token_store):
    items = [{"item_id": "itm_023", "qty": 1}]
    outcome = st.place_order(repo, token_store, "u_lowbalance", "rst_07", items, confirm_token=None)
    assert outcome.decision == Decision.BLOCKED
    assert outcome.gate_result.requirement == GateRequirement.SUFFICIENT_FUNDS

def test_prompt_6_age_gate_before_min_order(repo, token_store):
    items = [{"item_id": "itm_025", "qty": 1}]
    outcome = st.place_order(repo, token_store, "u_unverified", "rst_07", items, confirm_token=None)
    assert outcome.decision == Decision.BLOCKED
    assert outcome.gate_result.requirement == GateRequirement.AGE_18_PLUS