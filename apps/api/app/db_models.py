import uuid
from datetime import date as date_type
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResearchJobRecord(Base):
    __tablename__ = "research_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    requested_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class EvidenceRecord(Base):
    __tablename__ = "evidence"
    __table_args__ = (UniqueConstraint("ticker", "source_url", name="uq_evidence_ticker_source_url"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    document_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    model_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class FundamentalReportRecord(Base):
    __tablename__ = "fundamental_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(32), nullable=False, default="fundamental")
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[list] = mapped_column(PG_ARRAY(Text), nullable=False)
    financial_health: Mapped[str] = mapped_column(Text, nullable=False)
    valuation_view: Mapped[str] = mapped_column(Text, nullable=False)
    catalysts: Mapped[list] = mapped_column(PG_ARRAY(Text), nullable=False)
    risks: Mapped[list] = mapped_column(PG_ARRAY(Text), nullable=False)
    evidence: Mapped[list] = mapped_column(PG_ARRAY(PG_UUID(as_uuid=True)), nullable=False)


class RedTeamReportRecord(Base):
    __tablename__ = "red_team_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(32), nullable=False, default="red_team")
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    independent_bear_case: Mapped[str] = mapped_column(Text, nullable=False)
    key_risks: Mapped[list] = mapped_column(PG_ARRAY(Text), nullable=False)
    thesis_challenges: Mapped[list] = mapped_column(PG_ARRAY(Text), nullable=False)
    weakest_point_in_thesis: Mapped[str] = mapped_column(Text, nullable=False)
    what_would_invalidate_the_bear_case: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(PG_ARRAY(PG_UUID(as_uuid=True)), nullable=False)


class PsychologyReportRecord(Base):
    __tablename__ = "psychology_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(String(32), nullable=False, default="psychology")
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    market_temperature: Mapped[int] = mapped_column(Integer, nullable=False)
    expectation_gap: Mapped[str] = mapped_column(Text, nullable=False)
    fear_of_loss: Mapped[float] = mapped_column(Float, nullable=False)
    fomo: Mapped[float] = mapped_column(Float, nullable=False)
    narrative_saturation: Mapped[float] = mapped_column(Float, nullable=False)
    crowding: Mapped[float] = mapped_column(Float, nullable=False)
    dominant_narrative: Mapped[str] = mapped_column(Text, nullable=False)
    differentiated_or_contrarian_view: Mapped[str] = mapped_column(Text, nullable=False)
    psychology_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    previous_state_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("psychology_reports.id"), nullable=True
    )
    evidence: Mapped[list] = mapped_column(PG_ARRAY(PG_UUID(as_uuid=True)), nullable=False)


class QuantMetricsRecord(Base):
    __tablename__ = "quant_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    benchmark_ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    sector_ticker: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    lookback_trading_days: Mapped[int] = mapped_column(Integer, nullable=False)
    as_of: Mapped[date_type] = mapped_column(Date, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    cumulative_return: Mapped[float] = mapped_column(Float, nullable=False)
    annualized_volatility: Mapped[float] = mapped_column(Float, nullable=False)
    beta: Mapped[float] = mapped_column(Float, nullable=False)
    correlation_to_benchmark: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False)
    cumulative_abnormal_return: Mapped[float] = mapped_column(Float, nullable=False)
    average_daily_volume: Mapped[float] = mapped_column(Float, nullable=False)
    sector_relative_return: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class RiskAssessmentRecord(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    annualized_volatility: Mapped[float] = mapped_column(Float, nullable=False)
    suggested_position_size_pct: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss_distance_pct: Mapped[float] = mapped_column(Float, nullable=False)
    max_position_pct_cap: Mapped[float] = mapped_column(Float, nullable=False)
    target_position_volatility_contribution_pct: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    existing_position_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    portfolio_max_position_pct_cap: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="10.0"
    )
    notes: Mapped[list] = mapped_column(PG_ARRAY(Text), nullable=False)


class TradeProposalRecord(Base):
    __tablename__ = "trade_proposals"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    model_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    action: Mapped[str] = mapped_column(String(16), nullable=False)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)
    catalyst: Mapped[str] = mapped_column(Text, nullable=False)
    expectation_gap: Mapped[str] = mapped_column(Text, nullable=False)
    risk_notes: Mapped[str] = mapped_column(Text, nullable=False)
    invalidation_conditions: Mapped[list] = mapped_column(PG_ARRAY(Text), nullable=False)
    uncertainties: Mapped[list] = mapped_column(PG_ARRAY(Text), nullable=False)

    entry_price_range: Mapped[Optional[list]] = mapped_column(PG_ARRAY(Float), nullable=True)
    position_size_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stop_loss_distance_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    fundamental_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    psychology_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    red_team_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    quant_metrics_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    risk_assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    evidence: Mapped[list] = mapped_column(PG_ARRAY(PG_UUID(as_uuid=True)), nullable=False)


class HumanDecisionRecord(Base):
    __tablename__ = "human_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    trade_proposal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by: Mapped[str] = mapped_column(String(255), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


class ShadowPositionRecord(Base):
    __tablename__ = "shadow_positions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    research_job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    trade_proposal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, unique=True
    )
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    frozen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price_as_of: Mapped[date_type] = mapped_column(Date, nullable=False)
