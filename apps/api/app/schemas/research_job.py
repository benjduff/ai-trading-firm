from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ResearchJobStatus(str, Enum):
    PENDING = "pending"
    EVIDENCE_INGESTED = "evidence_ingested"
    FUNDAMENTAL_ANALYSIS_COMPLETE = "fundamental_analysis_complete"
    PSYCHOLOGY_ANALYSIS_COMPLETE = "psychology_analysis_complete"
    RED_TEAM_ANALYSIS_COMPLETE = "red_team_analysis_complete"
    QUANT_ANALYSIS_COMPLETE = "quant_analysis_complete"
    RISK_ASSESSMENT_COMPLETE = "risk_assessment_complete"
    TRADE_PROPOSAL_COMPLETE = "trade_proposal_complete"


class ResearchJob(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    ticker: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ResearchJobStatus = ResearchJobStatus.PENDING
    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requested_by: Optional[str] = None
