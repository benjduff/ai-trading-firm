from typing import Optional

from pydantic import BaseModel

from app.schemas.evidence import Evidence
from app.schemas.fundamental import FundamentalReport
from app.schemas.human_decision import HumanDecision
from app.schemas.psychology import PsychologyReport
from app.schemas.quant import QuantMetrics
from app.schemas.red_team import RedTeamReport
from app.schemas.research_job import ResearchJob
from app.schemas.risk import RiskAssessment
from app.schemas.trade_proposal import TradeProposal


class ResearchSummary(BaseModel):
    """Read-model aggregation for the human decision dashboard. Not persisted -
    assembled on request from the underlying tables."""

    job: ResearchJob
    evidence: list[Evidence]
    fundamental_report: Optional[FundamentalReport] = None
    psychology_report: Optional[PsychologyReport] = None
    red_team_report: Optional[RedTeamReport] = None
    quant_metrics: Optional[QuantMetrics] = None
    risk_assessment: Optional[RiskAssessment] = None
    trade_proposal: Optional[TradeProposal] = None
    human_decision: Optional[HumanDecision] = None
