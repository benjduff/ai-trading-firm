from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class RiskAssessment(BaseModel):
    """Deterministic single-trade sizing/stop guidance computed from QuantMetrics
    plus current portfolio state (queried from apps/execution over HTTP). No LLM
    is involved - see app/quant/risk.py. v2: adds a per-ticker concentration
    check against existing positions; still no correlation-across-holdings or
    portfolio-level VaR - a further extension once that's needed."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    research_job_id: UUID
    ticker: str
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    annualized_volatility: float
    suggested_position_size_pct: float
    stop_loss_distance_pct: float
    max_position_pct_cap: float
    target_position_volatility_contribution_pct: float
    existing_position_pct: Optional[float] = None
    portfolio_max_position_pct_cap: float
    notes: list[str] = Field(default_factory=list)
