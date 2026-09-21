from typing import Optional

from pydantic import BaseModel


class Position(BaseModel):
    """Mirrors the execution service's wire contract - see ExecutedOrder for why
    this isn't shared code."""

    ticker: str
    quantity: int
    average_entry_price: float
    cost_basis: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    price_error: Optional[str] = None


class AccountSummary(BaseModel):
    equity: float
    total_market_value: float
    total_unrealized_pnl: float
    exposure_pct: float
    position_count: int
    positions: list[Position]
