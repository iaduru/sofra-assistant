import pytest
from sofra.models.data_models import Restaurant, MenuItem, CartItem, User
from sofra.tools.money import quote_checkout, is_payment_sufficient

@pytest.fixture
def burger_stop() -> Restaurant:
    return Restaurant(
        id="rst_04",
        name="Burger Stop",
        cuisine="Fast Food",
        city="İstanbul",
        rating=3.9,
        delivery_fee_try=25,
        min_order_try=100,
        eta_min=30,
        district="Kadıköy",
        delivery_districts=["Kadıköy", "Ataşehir"],
        menu=[
            MenuItem(item_id="itm_013", name="Cheeseburger", price_try=195, category="main"),
            MenuItem(item_id="itm_014", name="Patates Kızartması", price_try=65, category="side"),
            MenuItem(item_id="itm_015", name="Milkshake", price_try=85, category="beverage"),
            MenuItem(item_id="itm_099", name="Deneme Ürünü", price_try=10, category="side", available=False),
        ],
    )

class TestQuoteCheckout:
    def test_prompt_3_scenario_add_to_existing_cart(self, burger_stop):
        items = [
            CartItem(item_id="itm_014", qty=1),
            CartItem(item_id="itm_015", qty=1),
            CartItem(item_id="itm_013", qty=2),
        ]
        quote = quote_checkout(burger_stop, items)
        assert quote.subtotal_try == 540
        assert quote.delivery_fee_try == 0
        assert quote.total_try == 540
        assert quote.meets_minimum is True

    def test_prompt_3_scenario_only_requested_items(self, burger_stop):
        items = [CartItem(item_id="itm_013", qty=2)]
        quote = quote_checkout(burger_stop, items)
        assert quote.subtotal_try == 390
        assert quote.delivery_fee_try == 0
        assert quote.total_try == 390

    def test_delivery_fee_applies_below_threshold(self, burger_stop):
        items = [CartItem(item_id="itm_014", qty=1)]
        quote = quote_checkout(burger_stop, items)
        assert quote.subtotal_try == 65
        assert quote.delivery_fee_try == 25
        assert quote.total_try == 90
        assert quote.meets_minimum is False

    def test_delivery_fee_free_exactly_at_threshold(self, burger_stop):
        items = [CartItem(item_id="itm_013", qty=1), CartItem(item_id="itm_014", qty=1)]
        quote = quote_checkout(burger_stop, items)
        assert quote.subtotal_try == 260
        assert quote.delivery_fee_try == 0

    def test_unavailable_item_raises_value_error(self, burger_stop):
        items = [CartItem(item_id="itm_099", qty=1)]
        with pytest.raises(ValueError):
            quote_checkout(burger_stop, [CartItem(item_id="itm_does_not_exist", qty=1)])

class TestPaymentSufficiency:
    def test_wallet_covers_total(self):
        user = User(
            id="u1", display_name="Test", wallet_balance_try=500,
            payment_method=False, age_verified=True, address="x", district="Kadıköy",
        )
        assert is_payment_sufficient(user, 300) is True

    def test_wallet_short_but_card_covers_remainder(self):
        user = User(
            id="u1", display_name="Test", wallet_balance_try=100,
            payment_method=True, age_verified=True, address="x", district="Kadıköy",
        )
        assert is_payment_sufficient(user, 300) is True

    def test_wallet_short_and_no_card_is_insufficient(self):
        user = User(
            id="u_lowbalance", display_name="Ece Kaya", wallet_balance_try=30,
            payment_method=False, age_verified=True, address="x", district="Şişli",
        )
        assert is_payment_sufficient(user, 320) is False