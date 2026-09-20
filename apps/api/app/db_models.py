import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
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
