from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TradeAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TradeProposal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    research_job_id: UUID
    ticker: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    action: TradeAction
    thesis: str
    catalyst: str
    expectation_gap: str
    risk_notes: str
    invalidation_conditions: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)

    entry_price_range: Optional[tuple[float, float]] = None
    position_size_pct: Optional[float] = None

    fundamental_report_id: Optional[UUID] = None
    psychology_report_id: Optional[UUID] = None
    red_team_report_id: Optional[UUID] = None
    evidence: list[UUID] = Field(default_factory=list)
