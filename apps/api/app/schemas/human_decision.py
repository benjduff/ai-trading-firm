from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class HumanDecisionAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    WATCH = "watch"
    REQUEST_MORE_RESEARCH = "request_more_research"


class HumanDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    research_job_id: UUID
    trade_proposal_id: UUID
    action: HumanDecisionAction
    reasoning: str
    decided_by: str
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
