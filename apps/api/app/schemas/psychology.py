from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.agent_report import AgentReport, AgentType


class PsychologyReport(AgentReport):
    agent_type: AgentType = AgentType.PSYCHOLOGY

    market_temperature: int = Field(ge=-5, le=5)
    expectation_gap: str
    fear_of_loss: float = Field(ge=0, le=1)
    fomo: float = Field(ge=0, le=1)
    narrative_saturation: float = Field(ge=0, le=1)
    crowding: float = Field(ge=0, le=1)
    dominant_narrative: str
    differentiated_or_contrarian_view: str
    psychology_confidence: float = Field(ge=0, le=1)
    previous_state_id: Optional[UUID] = None
