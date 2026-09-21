from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from app.portfolio import compute_positions

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass
class FakeOrder:
    ticker: str
    side: str
    quantity: int
    filled_price: float
    submitted_at: datetime
    status: str = "filled"


def test_two_buys_produce_a_weighted_average_price():
    orders = [
        FakeOrder("TEST", "buy", 10, 100.0, BASE),
        FakeOrder("TEST", "buy", 10, 200.0, BASE + timedelta(days=1)),
    ]
    position = compute_positions(orders)[0]
    assert position.quantity == 20
    assert position.average_entry_price == pytest.approx(150.0)


def test_fully_closed_position_is_excluded():
    orders = [
        FakeOrder("TEST", "buy", 10, 100.0, BASE),
        FakeOrder("TEST", "sell", 10, 110.0, BASE + timedelta(days=1)),
    ]
    assert compute_positions(orders) == []


def test_partial_sell_realizes_pnl_without_changing_remaining_average_price():
    # this is the case a naive signed-cost-sum implementation got wrong: it
    # conflated the realized gain on the sold shares into the cost basis of the
    # shares still held, giving avg=86.67 instead of the correct 100.0
    orders = [
        FakeOrder("TEST", "buy", 10, 100.0, BASE),
        FakeOrder("TEST", "sell", 4, 120.0, BASE + timedelta(days=1)),
    ]
    position = compute_positions(orders)[0]
    assert position.quantity == 6
    assert position.average_entry_price == pytest.approx(100.0)
    assert position.cost_basis == pytest.approx(600.0)


def test_sell_larger_than_the_long_position_flips_to_short():
    orders = [
        FakeOrder("TEST", "buy", 10, 100.0, BASE),
        FakeOrder("TEST", "sell", 15, 120.0, BASE + timedelta(days=1)),
    ]
    position = compute_positions(orders)[0]
    assert position.quantity == -5
    # the flipped-into short quantity opens fresh at the flip fill price
    assert position.average_entry_price == pytest.approx(120.0)


def test_result_is_independent_of_the_order_rows_are_fetched_in():
    chronological = [
        FakeOrder("TEST", "buy", 10, 100.0, BASE),
        FakeOrder("TEST", "sell", 4, 120.0, BASE + timedelta(days=1)),
    ]
    reversed_fetch_order = list(reversed(chronological))

    forward = compute_positions(chronological)[0]
    backward = compute_positions(reversed_fetch_order)[0]
    assert forward.quantity == backward.quantity
    assert forward.average_entry_price == pytest.approx(backward.average_entry_price)


def test_unfilled_orders_are_excluded():
    orders = [FakeOrder("TEST", "buy", 10, 100.0, BASE, status="rejected")]
    assert compute_positions(orders) == []


def test_orders_missing_a_fill_price_are_excluded():
    orders = [FakeOrder("TEST", "buy", 10, None, BASE, status="filled")]
    assert compute_positions(orders) == []


def test_pure_short_position():
    orders = [FakeOrder("TEST", "sell", 5, 50.0, BASE)]
    position = compute_positions(orders)[0]
    assert position.quantity == -5
    assert position.average_entry_price == pytest.approx(50.0)


def test_adding_to_an_existing_short_averages_correctly():
    orders = [
        FakeOrder("TEST", "sell", 5, 50.0, BASE),
        FakeOrder("TEST", "sell", 5, 70.0, BASE + timedelta(days=1)),
    ]
    position = compute_positions(orders)[0]
    assert position.quantity == -10
    assert position.average_entry_price == pytest.approx(60.0)


def test_positions_across_different_tickers_are_independent():
    orders = [
        FakeOrder("AAA", "buy", 10, 100.0, BASE),
        FakeOrder("BBB", "buy", 5, 50.0, BASE),
    ]
    positions = {p.ticker: p for p in compute_positions(orders)}
    assert set(positions) == {"AAA", "BBB"}
    assert positions["AAA"].quantity == 10
    assert positions["BBB"].quantity == 5
