from pydantic import BaseModel

from app.schemas.agent_report import AgentReport, AgentType


class FundamentalAnalysis(BaseModel):
    """Fields the LLM is asked to produce for a fundamental report."""

    summary: str
    key_findings: list[str]
    financial_health: str
    valuation_view: str
    catalysts: list[str]
    risks: list[str]


class FundamentalReport(AgentReport):
    agent_type: AgentType = AgentType.FUNDAMENTAL

    key_findings: list[str]
    financial_health: str
    valuation_view: str
    catalysts: list[str]
    risks: list[str]
