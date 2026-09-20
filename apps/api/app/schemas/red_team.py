from pydantic import BaseModel

from app.schemas.agent_report import AgentReport, AgentType


class RedTeamIndependentView(BaseModel):
    """Step 1: the bear case formed from evidence alone, before seeing the thesis."""

    bear_case: str
    key_risks: list[str]


class RedTeamChallenge(BaseModel):
    """Step 2: the critique of the Fundamental thesis, informed by step 1."""

    summary: str
    thesis_challenges: list[str]
    weakest_point_in_thesis: str
    what_would_invalidate_the_bear_case: str


class RedTeamReport(AgentReport):
    agent_type: AgentType = AgentType.RED_TEAM

    independent_bear_case: str
    key_risks: list[str]
    thesis_challenges: list[str]
    weakest_point_in_thesis: str
    what_would_invalidate_the_bear_case: str
