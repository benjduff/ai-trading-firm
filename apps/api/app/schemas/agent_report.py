from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    FUNDAMENTAL = "fundamental"
    PSYCHOLOGY = "psychology"
    RED_TEAM = "red_team"
    RISK = "risk"
    CIO = "cio"
    SCOUT = "scout"


class AgentReport(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    research_job_id: UUID
    ticker: str
    agent_type: AgentType
    model_id: str
    prompt_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str
    evidence: list[UUID] = Field(default_factory=list)
