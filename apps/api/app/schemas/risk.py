from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class RiskAssessment(BaseModel):
    """Deterministic single-trade sizing/stop guidance computed from QuantMetrics.
    No LLM is involved - see app/quant/risk.py. v1: no portfolio-level limits yet
    (concentration, correlation across current holdings); those need tracked
    portfolio state that doesn't exist until paper trading."""

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
    notes: list[str] = Field(default_factory=list)
