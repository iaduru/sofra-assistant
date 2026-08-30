import pytest
from sofra import config
from sofra.data.repository import Repository

@pytest.fixture
def repo() -> Repository:
    return Repository(
        users_path=config.USERS_PATH,
        restaurants_path=config.RESTAURANTS_PATH,
        carts_path=config.CARTS_PATH,
        orders_path=config.ORDERS_PATH,
    )

class TestReads:
    def test_get_user_existing(self, repo):
        user = repo.get_user("u_ok")
        assert user is not None
        assert user.display_name == "Deniz Yılmaz"

    def test_get_user_missing_returns_none(self, repo):
        assert repo.get_user("does_not_exist") is None

    def test_get_restaurant(self, repo):
        r = repo.get_restaurant("rst_04")
        assert r is not None
        assert r.name == "Burger Stop"

    def test_search_restaurants_prompt_2_scenario(self, repo):
        results = repo.search_restaurants(cuisine="Italian", near_district="Kadıköy")
        names = sorted(r.name for r in results)
        assert names == ["Napoli Fırın", "Pizza Locale"]

    def test_search_restaurants_near_district_filters_correctly(self, repo):
        results = repo.search_restaurants(near_district="Üsküdar")
        names = [r.name for r in results]
        assert "Ege Balık" not in names

    def test_get_cart(self, repo):
        cart = repo.get_cart("u_ok")
        assert cart is not None
        assert cart.restaurant_id == "rst_04"
        assert len(cart.items) == 2

    def test_list_orders_count(self, repo):
        orders = repo.list_orders("u_ok")
        assert len(orders) == 10

    def test_get_order_found(self, repo):
        order = repo.get_order("u_ok", "u_ok_o9")
        assert order is not None
        assert order.status == "received"

    def test_get_order_not_found(self, repo):
        assert repo.get_order("u_ok", "does_not_exist") is None

    def test_get_order_wrong_user_returns_none(self, repo):
        assert repo.get_order("u_unverified", "u_ok_o9") is None

class TestMutations:
    def test_create_order_appends_and_returns_new_order(self, repo):
        before = len(repo.list_orders("u_ok"))
        order = repo.create_order(
            user_id="u_ok", restaurant_name="Burger Stop", total_try=390, date="2026-08-20"
        )
        after = len(repo.list_orders("u_ok"))
        assert after == before + 1
        assert order.status == "received"
        assert order.total_try == 390
        existing_ids = {o.order_id for o in repo.list_orders("u_ok")}
        assert len(existing_ids) == after

    def test_cancel_order_changes_status(self, repo):
        order = repo.cancel_order("u_ok", "u_ok_o9")
        assert order is not None
        assert order.status == "cancelled"
        assert repo.get_order("u_ok", "u_ok_o9").status == "cancelled"

    def test_cancel_order_missing_returns_none(self, repo):
        assert repo.cancel_order("u_ok", "does_not_exist") is None

    def test_add_tip_accumulates_not_overwrites(self, repo):
        order = repo.get_order("u_ok", "u_ok_o9")
        assert order.tip_try == 0.0

        repo.add_tip("u_ok", "u_ok_o9", 20.0)
        assert repo.get_order("u_ok", "u_ok_o9").tip_try == 20.0

        repo.add_tip("u_ok", "u_ok_o9", 15.0)
        assert repo.get_order("u_ok", "u_ok_o9").tip_try == 35.0

    def test_mutation_in_one_repo_does_not_leak_to_another(self, repo):
        repo.cancel_order("u_ok", "u_ok_o9")
        fresh_repo = Repository(
            users_path=config.USERS_PATH,
            restaurants_path=config.RESTAURANTS_PATH,
            carts_path=config.CARTS_PATH,
            orders_path=config.ORDERS_PATH,
        )
        assert fresh_repo.get_order("u_ok", "u_ok_o9").status == "received"