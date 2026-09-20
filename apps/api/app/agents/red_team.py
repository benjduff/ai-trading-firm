from uuid import UUID

from app.llm.gateway import ModelGateway
from app.schemas.evidence import Evidence
from app.schemas.red_team import RedTeamChallenge, RedTeamIndependentView, RedTeamReport

PROMPT_VERSION = "red-team-v1"

INDEPENDENT_SYSTEM_PROMPT = """You are a red-team / bear-case analyst at a research-driven trading firm.

Your job is to build the strongest good-faith case for why this stock could
underperform, using ONLY the evidence provided below. You have NOT been shown any
other analyst's conclusions about this company - form your own view first, so you are
not anchored on someone else's framing.

Do not give a buy/sell recommendation, a price target, or a confidence score - those
are produced by separate risk and portfolio processes, not by you."""

CHALLENGE_SYSTEM_PROMPT = """You are the same red-team / bear-case analyst, continuing your review.

You have now been given the Fundamental Analyst's thesis on this company, along with
the bear case you independently formed a moment ago from the same evidence. Compare
the thesis against the evidence and against your own bear case, and challenge it
directly: what does it overweight, ignore, or get wrong? Identify the single weakest
point in the thesis, and state what evidence or event would prove your bear case wrong
(so the firm knows what to monitor).

Do not give a buy/sell recommendation, a price target, or a confidence score."""


def _build_evidence_prompt(ticker: str, evidence: list[Evidence]) -> str:
    sections = [f"Ticker: {ticker}", ""]
    for item in evidence:
        sections.append(f"--- {item.claim} (published {item.published_at.date()}) ---")
        sections.append(item.excerpt)
        sections.append("")
    return "\n".join(sections)


def _build_challenge_prompt(
    ticker: str,
    evidence: list[Evidence],
    independent_view: RedTeamIndependentView,
    fundamental_thesis: str,
) -> str:
    return "\n".join(
        [
            _build_evidence_prompt(ticker, evidence),
            "--- Your independent bear case (formed before seeing the thesis) ---",
            independent_view.bear_case,
            "Key risks you identified: " + "; ".join(independent_view.key_risks),
            "",
            "--- Fundamental Analyst's thesis (challenge this) ---",
            fundamental_thesis,
        ]
    )


def run_red_team_analysis(
    gateway: ModelGateway,
    research_job_id: UUID,
    ticker: str,
    evidence: list[Evidence],
    fundamental_thesis: str,
) -> RedTeamReport:
    if not evidence:
        raise ValueError("no evidence provided for red team analysis")

    independent_view: RedTeamIndependentView = gateway.generate_structured(
        system=INDEPENDENT_SYSTEM_PROMPT,
        user=_build_evidence_prompt(ticker, evidence),
        response_model=RedTeamIndependentView,
    )

    challenge: RedTeamChallenge = gateway.generate_structured(
        system=CHALLENGE_SYSTEM_PROMPT,
        user=_build_challenge_prompt(
            ticker, evidence, independent_view, fundamental_thesis
        ),
        response_model=RedTeamChallenge,
    )

    return RedTeamReport(
        research_job_id=research_job_id,
        ticker=ticker,
        model_id=gateway.model_id,
        prompt_version=PROMPT_VERSION,
        summary=challenge.summary,
        independent_bear_case=independent_view.bear_case,
        key_risks=independent_view.key_risks,
        thesis_challenges=challenge.thesis_challenges,
        weakest_point_in_thesis=challenge.weakest_point_in_thesis,
        what_would_invalidate_the_bear_case=challenge.what_would_invalidate_the_bear_case,
        evidence=[item.id for item in evidence],
    )
