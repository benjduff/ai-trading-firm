from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TradeAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class CIOSynthesis(BaseModel):
    """Fields the LLM is asked to produce. Numeric sizing/stop come from the
    deterministic RiskAssessment instead, per CLAUDE.md's non-negotiable rule."""

    action: TradeAction
    thesis: str
    catalyst: str
    expectation_gap: str
    risk_notes: str
    invalidation_conditions: list[str]
    uncertainties: list[str]


class TradeProposal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    research_job_id: UUID
    ticker: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_id: Optional[str] = None
    prompt_version: Optional[str] = None

    action: TradeAction
    thesis: str
    catalyst: str
    expectation_gap: str
    risk_notes: str
    invalidation_conditions: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)

    entry_price_range: Optional[tuple[float, float]] = None
    position_size_pct: Optional[float] = None
    stop_loss_distance_pct: Optional[float] = None

    fundamental_report_id: Optional[UUID] = None
    psychology_report_id: Optional[UUID] = None
    red_team_report_id: Optional[UUID] = None
    quant_metrics_id: Optional[UUID] = None
    risk_assessment_id: Optional[UUID] = None
    evidence: list[UUID] = Field(default_factory=list)
