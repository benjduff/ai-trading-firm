from uuid import UUID

from app.llm.gateway import ModelGateway
from app.schemas.evidence import Evidence
from app.schemas.fundamental import FundamentalAnalysis, FundamentalReport

PROMPT_VERSION = "fundamental-v1"

SYSTEM_PROMPT = """You are a fundamental equity analyst at a research-driven trading firm.

You are given excerpts from a company's SEC filings (10-K, 10-Q, 8-K). Analyze the
company's fundamentals using ONLY the evidence provided below - do not rely on
outside knowledge or invent facts not supported by the excerpts.

Do not give a buy/sell recommendation, a price target, or a confidence score - those
are produced by separate risk and portfolio processes, not by you.

Focus on: financial health and trajectory, and any catalysts or risks visible in the
filings."""


def _build_user_prompt(ticker: str, evidence: list[Evidence]) -> str:
    sections = [f"Ticker: {ticker}", ""]
    for item in evidence:
        sections.append(f"--- {item.claim} (published {item.published_at.date()}) ---")
        sections.append(item.excerpt)
        sections.append("")
    return "\n".join(sections)


def run_fundamental_analysis(
    gateway: ModelGateway,
    research_job_id: UUID,
    ticker: str,
    evidence: list[Evidence],
) -> FundamentalReport:
    if not evidence:
        raise ValueError("no evidence provided for fundamental analysis")

    analysis: FundamentalAnalysis = gateway.generate_structured(
        system=SYSTEM_PROMPT,
        user=_build_user_prompt(ticker, evidence),
        response_model=FundamentalAnalysis,
    )

    return FundamentalReport(
        research_job_id=research_job_id,
        ticker=ticker,
        model_id=gateway.model_id,
        prompt_version=PROMPT_VERSION,
        summary=analysis.summary,
        key_findings=analysis.key_findings,
        financial_health=analysis.financial_health,
        valuation_view=analysis.valuation_view,
        catalysts=analysis.catalysts,
        risks=analysis.risks,
        evidence=[item.id for item in evidence],
    )
