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
