from uuid import UUID

from app.llm.gateway import ModelGateway
from app.schemas.fundamental import FundamentalReport
from app.schemas.psychology import PsychologyReport
from app.schemas.quant import QuantMetrics
from app.schemas.red_team import RedTeamReport
from app.schemas.risk import RiskAssessment
from app.schemas.trade_proposal import CIOSynthesis, TradeProposal

PROMPT_VERSION = "cio-v1"

SYSTEM_PROMPT = """You are the CIO (Chief Investment Officer) synthesizer at a
research-driven trading firm. You combine the Fundamental Analyst's thesis, the
Psychology Analyst's independent read of market sentiment, the Red Team's independent
bear case and challenge, and deterministic Quant/Risk metrics into one structured
trade proposal.

You synthesize; you do NOT do new research. Do not introduce facts, catalysts, or
risks that are not present in the materials given to you below. Where the analysts
disagree, say so explicitly rather than picking a side silently - the human reviewer
needs to see the disagreement, not a false consensus.

You choose the proposed action (buy / sell / hold). This is a PROPOSAL for a human to
approve, reject, or send back for more research - you are not executing anything and
you should not imply certainty you don't have. Do not give a confidence score or a
price target. Position sizing and stop-loss distance are provided to you as fixed
numbers from the deterministic Risk Assessment - reference them in your risk_notes,
but do not invent or contradict them."""


def _format_report_block(title: str, body: str) -> str:
    return f"--- {title} ---\n{body}\n"


def _build_user_prompt(
    ticker: str,
    fundamental: FundamentalReport,
    psychology: PsychologyReport,
    red_team: RedTeamReport,
    quant: QuantMetrics,
    risk: RiskAssessment,
) -> str:
    sections = [f"Ticker: {ticker}", ""]

    sections.append(
        _format_report_block(
            "Fundamental Analyst",
            "\n".join(
                [
                    f"Summary: {fundamental.summary}",
                    "Key findings: " + "; ".join(fundamental.key_findings),
                    f"Financial health: {fundamental.financial_health}",
                    f"Valuation view: {fundamental.valuation_view}",
                    "Catalysts: " + "; ".join(fundamental.catalysts),
                    "Risks: " + "; ".join(fundamental.risks),
                ]
            ),
        )
    )

    sections.append(
        _format_report_block(
            "Psychology Analyst (formed independently of Fundamental)",
            "\n".join(
                [
                    f"Summary: {psychology.summary}",
                    f"Market temperature (-5 panic..+5 euphoria): {psychology.market_temperature}",
                    f"Expectation gap: {psychology.expectation_gap}",
                    f"Dominant narrative: {psychology.dominant_narrative}",
                    f"Differentiated/contrarian view: {psychology.differentiated_or_contrarian_view}",
                    f"Fear of loss: {psychology.fear_of_loss:.2f}, FOMO: {psychology.fomo:.2f}, "
                    f"Narrative saturation: {psychology.narrative_saturation:.2f}, "
                    f"Crowding: {psychology.crowding:.2f}",
                ]
            ),
        )
    )

    sections.append(
        _format_report_block(
            "Red Team (independent bear case, then challenged the Fundamental thesis)",
            "\n".join(
                [
                    f"Independent bear case: {red_team.independent_bear_case}",
                    "Key risks: " + "; ".join(red_team.key_risks),
                    "Thesis challenges: " + "; ".join(red_team.thesis_challenges),
                    f"Weakest point in thesis: {red_team.weakest_point_in_thesis}",
                    f"What would invalidate the bear case: {red_team.what_would_invalidate_the_bear_case}",
                ]
            ),
        )
    )

    sections.append(
        _format_report_block(
            "Quant (deterministic)",
            "\n".join(
                [
                    f"As of: {quant.as_of}, lookback: {quant.lookback_trading_days} trading days",
                    f"Cumulative return: {quant.cumulative_return:.2%}",
                    f"Annualized volatility: {quant.annualized_volatility:.2%}",
                    f"Beta vs {quant.benchmark_ticker}: {quant.beta:.2f}",
                    f"Correlation to {quant.benchmark_ticker}: {quant.correlation_to_benchmark:.2f}",
                    f"Max drawdown: {quant.max_drawdown:.2%}",
                    f"Cumulative abnormal return: {quant.cumulative_abnormal_return:.2%}",
                    (
                        f"Sector-relative return vs {quant.sector_ticker}: {quant.sector_relative_return:.2%}"
                        if quant.sector_ticker and quant.sector_relative_return is not None
                        else "Sector-relative return: not computed"
                    ),
                ]
            ),
        )
    )

    sections.append(
        _format_report_block(
            "Risk (deterministic - fixed numbers, do not change)",
            "\n".join(
                [
                    f"Suggested position size: {risk.suggested_position_size_pct:.2f}% of portfolio "
                    f"(cap {risk.max_position_pct_cap:.2f}%)",
                    f"Stop-loss distance: {risk.stop_loss_distance_pct:.2f}%",
                    "Notes: " + ("; ".join(risk.notes) if risk.notes else "none"),
                ]
            ),
        )
    )

    return "\n".join(sections)


def run_cio_synthesis(
    gateway: ModelGateway,
    research_job_id: UUID,
    ticker: str,
    fundamental: FundamentalReport,
    psychology: PsychologyReport,
    red_team: RedTeamReport,
    quant: QuantMetrics,
    risk: RiskAssessment,
) -> TradeProposal:
    synthesis: CIOSynthesis = gateway.generate_structured(
        system=SYSTEM_PROMPT,
        user=_build_user_prompt(ticker, fundamental, psychology, red_team, quant, risk),
        response_model=CIOSynthesis,
    )

    combined_evidence = sorted(
        set(fundamental.evidence) | set(psychology.evidence) | set(red_team.evidence)
    )

    return TradeProposal(
        research_job_id=research_job_id,
        ticker=ticker,
        model_id=gateway.model_id,
        prompt_version=PROMPT_VERSION,
        action=synthesis.action,
        thesis=synthesis.thesis,
        catalyst=synthesis.catalyst,
        expectation_gap=synthesis.expectation_gap,
        risk_notes=synthesis.risk_notes,
        invalidation_conditions=synthesis.invalidation_conditions,
        uncertainties=synthesis.uncertainties,
        position_size_pct=risk.suggested_position_size_pct,
        stop_loss_distance_pct=risk.stop_loss_distance_pct,
        fundamental_report_id=fundamental.id,
        psychology_report_id=psychology.id,
        red_team_report_id=red_team.id,
        quant_metrics_id=quant.id,
        risk_assessment_id=risk.id,
        evidence=combined_evidence,
    )
