from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class QuantMetrics(BaseModel):
    """Deterministic quant metrics for a ticker. Computed entirely by
    app/quant/risk_metrics.py - no LLM is involved anywhere in this schema,
    per CLAUDE.md's non-negotiable rule (LLMs interpret, deterministic Python
    calculates)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    research_job_id: UUID
    ticker: str
    benchmark_ticker: str
    sector_ticker: Optional[str] = None
    lookback_trading_days: int
    as_of: date
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    cumulative_return: float
    annualized_volatility: float
    beta: float
    correlation_to_benchmark: float
    max_drawdown: float
    cumulative_abnormal_return: float
    average_daily_volume: float
    sector_relative_return: Optional[float] = None
