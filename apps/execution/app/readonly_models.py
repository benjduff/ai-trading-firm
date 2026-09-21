"""Read-only views onto tables owned and migrated by apps/api. This service
never writes to them and does not import apps/api's Python package - only these
two tables' names/columns are shared, so there is no code path from this
service back into the LLM-driven research pipeline.

These use their own DeclarativeBase, deliberately separate from app.db.Base
(which Alembic's target_metadata points at). If these were on the same Base,
autogenerate would see "metadata wants a trade_proposals table, the reflected
DB doesn't have one" (since we only reflect this service's owned tables) and
generate a CREATE TABLE - or worse, drop columns this service's slim model
doesn't define. A separate Base means Alembic never sees them at all, while a
plain SQLAlchemy Session can still query classes from either Base freely."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ReadOnlyBase(DeclarativeBase):
    pass


class TradeProposalRecord(ReadOnlyBase):
    __tablename__ = "trade_proposals"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    research_job_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True))
    ticker: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    action: Mapped[str] = mapped_column(String(16))
    position_size_pct: Mapped[Optional[float]] = mapped_column(Float)
    stop_loss_distance_pct: Mapped[Optional[float]] = mapped_column(Float)


class HumanDecisionRecord(ReadOnlyBase):
    __tablename__ = "human_decisions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    research_job_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True))
    trade_proposal_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(32))
    decided_by: Mapped[str] = mapped_column(String(255))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
