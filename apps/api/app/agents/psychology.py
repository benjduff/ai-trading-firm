from typing import Optional
from uuid import UUID

from app.llm.gateway import ModelGateway
from app.schemas.evidence import Evidence
from app.schemas.psychology import PsychologyAnalysis, PsychologyReport

PROMPT_VERSION = "psychology-v1"

SYSTEM_PROMPT = """You are a market psychology analyst at a research-driven trading firm.

Your job is to assess what the market currently believes about this company, how
strongly, and what is already priced in - NOT whether the fundamentals are good.
You are intentionally not shown any other analyst's conclusions about this company;
form your own independent view so the firm gets an unbiased read rather than one
analyst anchoring on another.

You are given excerpts from the company's recent SEC filings (10-K, 10-Q, 8-K). These
are an incomplete proxy for market sentiment - dedicated news/social-sentiment
ingestion has not been built yet - so also draw on your general knowledge of how the
market currently perceives this company or its sector (narrative, hype cycles, analyst
tone) where relevant, and be explicit in your reasoning about which parts are
evidence-grounded versus general market awareness.

Central concept: the expectation gap = your forward view minus the market's implied
view. Extreme sentiment is not itself a timing signal - do not recommend a trade or
generate a contrarian call purely because sentiment is extreme. Do not give a buy/sell
recommendation or a price target."""


def _build_user_prompt(ticker: str, evidence: list[Evidence]) -> str:
    sections = [f"Ticker: {ticker}", ""]
    for item in evidence:
        sections.append(f"--- {item.claim} (published {item.published_at.date()}) ---")
        sections.append(item.excerpt)
        sections.append("")
    return "\n".join(sections)


def run_psychology_analysis(
    gateway: ModelGateway,
    research_job_id: UUID,
    ticker: str,
    evidence: list[Evidence],
    previous_state_id: Optional[UUID] = None,
) -> PsychologyReport:
    if not evidence:
        raise ValueError("no evidence provided for psychology analysis")

    analysis: PsychologyAnalysis = gateway.generate_structured(
        system=SYSTEM_PROMPT,
        user=_build_user_prompt(ticker, evidence),
        response_model=PsychologyAnalysis,
    )

    return PsychologyReport(
        research_job_id=research_job_id,
        ticker=ticker,
        model_id=gateway.model_id,
        prompt_version=PROMPT_VERSION,
        summary=analysis.summary,
        market_temperature=analysis.market_temperature,
        expectation_gap=analysis.expectation_gap,
        fear_of_loss=analysis.fear_of_loss,
        fomo=analysis.fomo,
        narrative_saturation=analysis.narrative_saturation,
        crowding=analysis.crowding,
        dominant_narrative=analysis.dominant_narrative,
        differentiated_or_contrarian_view=analysis.differentiated_or_contrarian_view,
        psychology_confidence=analysis.psychology_confidence,
        previous_state_id=previous_state_id,
        evidence=[item.id for item in evidence],
    )
