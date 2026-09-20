"""Deterministic position sizing / stop-loss heuristics. No LLM involved,
per CLAUDE.md's non-negotiable rule: LLMs interpret, deterministic Python
calculates. Reuses Quant's already-computed volatility/drawdown - does not
fetch new data or do new research.

v1: single-trade sizing only. No portfolio-level limits (concentration,
correlation across current holdings, capital-at-risk budgets) - those need
tracked portfolio state, which doesn't exist until paper trading (Phase 12).
Extend this module then rather than replacing it."""

import math
from uuid import UUID

from app.schemas.quant import QuantMetrics
from app.schemas.risk import RiskAssessment

TRADING_DAYS_PER_YEAR = 252

DEFAULT_MAX_POSITION_PCT = 5.0
DEFAULT_TARGET_VOL_CONTRIBUTION_PCT = 1.0
DEFAULT_STOP_LOSS_VOL_MULTIPLE = 2.0
DEFAULT_ASSUMED_HOLDING_DAYS = 10

HIGH_DRAWDOWN_THRESHOLD = -0.30


def assess_risk(
    research_job_id: UUID,
    ticker: str,
    quant_metrics: QuantMetrics,
    max_position_pct: float = DEFAULT_MAX_POSITION_PCT,
    target_vol_contribution_pct: float = DEFAULT_TARGET_VOL_CONTRIBUTION_PCT,
    stop_loss_vol_multiple: float = DEFAULT_STOP_LOSS_VOL_MULTIPLE,
    assumed_holding_days: int = DEFAULT_ASSUMED_HOLDING_DAYS,
) -> RiskAssessment:
    annualized_volatility = quant_metrics.annualized_volatility

    if annualized_volatility <= 0:
        suggested_position_size_pct = max_position_pct
    else:
        # target_vol_contribution_pct and the result are both percentage-points
        # (e.g. 1.0 = 1%); annualized_volatility is a fraction (e.g. 0.20 = 20%).
        # (target% / 100) / vol_fraction * 100 == target% / vol_fraction.
        vol_scaled_size_pct = target_vol_contribution_pct / annualized_volatility
        suggested_position_size_pct = min(max_position_pct, vol_scaled_size_pct)

    daily_volatility = annualized_volatility / math.sqrt(TRADING_DAYS_PER_YEAR)
    stop_loss_distance_pct = (
        stop_loss_vol_multiple * daily_volatility * math.sqrt(assumed_holding_days) * 100
    )

    notes = []
    if quant_metrics.max_drawdown <= HIGH_DRAWDOWN_THRESHOLD:
        notes.append(
            f"historical max drawdown over the lookback window was "
            f"{quant_metrics.max_drawdown:.1%}; size and stop reflect current "
            f"volatility only, not tail risk of a repeat drawdown"
        )
    if annualized_volatility <= 0:
        notes.append(
            "annualized volatility was zero or unavailable; position sizing "
            "fell back to the max position cap rather than vol-scaling"
        )

    return RiskAssessment(
        research_job_id=research_job_id,
        ticker=ticker.upper(),
        annualized_volatility=annualized_volatility,
        suggested_position_size_pct=suggested_position_size_pct,
        stop_loss_distance_pct=stop_loss_distance_pct,
        max_position_pct_cap=max_position_pct,
        target_position_volatility_contribution_pct=target_vol_contribution_pct,
        notes=notes,
    )
