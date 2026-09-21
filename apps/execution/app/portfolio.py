"""Derives current positions from filled executed_orders. No LLM involved -
deterministic Python, per CLAUDE.md's non-negotiable rule.

v1 uses average-cost accounting over signed quantities (buys positive, sells
negative). This is exact as long as every executed_orders row represents an
independent open (the common case today - there is no explicit "close this
position" flow yet); it becomes an approximation once partial closes are
common, at which point this should move to proper lot tracking."""

from dataclasses import dataclass, field
from typing import Optional

from app.broker import BrokerClient, BrokerError
from app.market_data import MarketDataError


@dataclass
class Position:
    ticker: str
    quantity: int
    average_entry_price: float
    cost_basis: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    price_error: Optional[str] = None


@dataclass
class AccountSummary:
    equity: float
    total_market_value: float
    total_unrealized_pnl: float
    exposure_pct: float
    position_count: int
    positions: list = field(default_factory=list)


def compute_positions(orders: list) -> list:
    """Sequential average-cost accounting, processed in fill order. A same-
    direction order (adding to a long, or to a short) extends the cost basis
    proportionally; an opposite-direction order realizes P&L on the closed
    portion at the position's existing average price, leaving the remaining
    shares' average cost unchanged - and opens a fresh position at the fill
    price for any quantity that flips past zero."""
    filled = [o for o in orders if o.status == "filled" and o.filled_price is not None]
    filled.sort(key=lambda o: o.submitted_at)

    by_ticker: dict = {}
    for order in filled:
        signed_qty = order.quantity if order.side == "buy" else -order.quantity
        agg = by_ticker.setdefault(order.ticker, {"quantity": 0, "cost": 0.0})
        prev_qty, prev_cost = agg["quantity"], agg["cost"]

        same_direction = prev_qty == 0 or (prev_qty > 0) == (signed_qty > 0)
        if same_direction:
            agg["quantity"] = prev_qty + signed_qty
            agg["cost"] = prev_cost + signed_qty * order.filled_price
        else:
            reduce_qty = min(abs(signed_qty), abs(prev_qty))
            avg_price = abs(prev_cost / prev_qty) if prev_qty else 0.0
            direction = 1 if prev_qty > 0 else -1
            agg["quantity"] = prev_qty + signed_qty
            agg["cost"] = prev_cost - (reduce_qty * avg_price * direction)

            leftover = abs(signed_qty) - reduce_qty
            if leftover > 0:
                flip_sign = 1 if signed_qty > 0 else -1
                agg["cost"] += flip_sign * leftover * order.filled_price

    positions = []
    for ticker, agg in by_ticker.items():
        if agg["quantity"] == 0:
            continue
        positions.append(
            Position(
                ticker=ticker,
                quantity=agg["quantity"],
                average_entry_price=agg["cost"] / agg["quantity"],
                cost_basis=abs(agg["cost"]),
            )
        )
    return positions


def _enrich_with_live_price(position: Position, broker: BrokerClient) -> None:
    try:
        price = broker.get_last_price(position.ticker)
    except (MarketDataError, BrokerError) as e:
        position.price_error = str(e)
        return

    position.current_price = price
    position.market_value = price * position.quantity
    position.unrealized_pnl = (price - position.average_entry_price) * position.quantity
    position.unrealized_pnl_pct = (
        position.unrealized_pnl / position.cost_basis if position.cost_basis else 0.0
    )


def get_positions(orders: list, broker: BrokerClient) -> list:
    positions = compute_positions(orders)
    for position in positions:
        _enrich_with_live_price(position, broker)
    return positions


def get_account_summary(orders: list, broker: BrokerClient) -> AccountSummary:
    positions = get_positions(orders, broker)
    equity = broker.get_account_equity()

    total_market_value = sum(p.market_value or 0.0 for p in positions)
    total_unrealized_pnl = sum(p.unrealized_pnl or 0.0 for p in positions)
    total_exposure = sum(abs(p.market_value or 0.0) for p in positions)

    return AccountSummary(
        equity=equity,
        total_market_value=total_market_value,
        total_unrealized_pnl=total_unrealized_pnl,
        exposure_pct=(total_exposure / equity * 100.0) if equity else 0.0,
        position_count=len(positions),
        positions=positions,
    )
