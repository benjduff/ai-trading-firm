from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ExecutedOrder(BaseModel):
    """Mirrors the execution service's wire contract. Deliberately its own
    definition, not shared code - the two services don't share Python types any
    more than they share database models."""

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
