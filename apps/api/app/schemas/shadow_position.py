from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.trade_proposal import TradeAction


class ShadowPosition(BaseModel):
    """A frozen, point-in-time snapshot of a TradeProposal's entry price, created
    automatically and unconditionally when the proposal is synthesized - before
    any human decision exists. This is what lets the firm grade its own calls
    (including rejected ones) against reality before risking real capital. Never
    created selectively; freezing must not depend on what a human later decides."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    research_job_id: UUID
    trade_proposal_id: UUID
    ticker: str
    action: TradeAction
    frozen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entry_price: float
    entry_price_as_of: date


class ShadowPerformanceResponse(BaseModel):
    shadow_position: ShadowPosition
    current_price: float
    current_price_as_of: date
    days_since_frozen: int
    raw_price_return_pct: float
    shadow_return_pct: float
    human_decision_action: Optional[str] = None
