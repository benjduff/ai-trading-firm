from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExecuteRequest(BaseModel):
    trade_proposal_id: UUID


class ExecutedOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trade_proposal_id: UUID
    human_decision_id: UUID
    ticker: str
    side: str
    quantity: int
    order_type: str
    broker: str
    broker_order_id: Optional[str] = None
    stop_loss_price: Optional[float] = None
    status: str
    submitted_at: datetime
    filled_price: Optional[float] = None
    filled_at: Optional[datetime] = None
    error: Optional[str] = None


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    quantity: int
    average_entry_price: float
    cost_basis: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    price_error: Optional[str] = None


class AccountSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    equity: float
    total_market_value: float
    total_unrealized_pnl: float
    exposure_pct: float
    position_count: int
    positions: list[PositionResponse]
