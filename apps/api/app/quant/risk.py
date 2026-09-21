"""Deterministic position sizing / stop-loss heuristics. No LLM involved,
per CLAUDE.md's non-negotiable rule: LLMs interpret, deterministic Python
calculates. Reuses Quant's already-computed volatility/drawdown - does not
fetch new data or do new research (except querying current portfolio state
from apps/execution over HTTP, which is existing fact, not research).

v2: adds a per-ticker concentration check against currently-held positions.
Still no correlation-across-holdings or portfolio-level VaR - extend this
module further once that's needed, rather than replacing it."""

import math
from typing import Optional
from uuid import UUID

import httpx

from app.config import settings
from app.schemas.quant import QuantMetrics
from app.schemas.risk import RiskAssessment

TRADING_DAYS_PER_YEAR = 252

DEFAULT_MAX_POSITION_PCT = 5.0
DEFAULT_TARGET_VOL_CONTRIBUTION_PCT = 1.0
DEFAULT_STOP_LOSS_VOL_MULTIPLE = 2.0
DEFAULT_ASSUMED_HOLDING_DAYS = 10
DEFAULT_PORTFOLIO_MAX_POSITION_PCT = 10.0

HIGH_DRAWDOWN_THRESHOLD = -0.30


def _fetch_existing_position_pct(ticker: str) -> Optional[float]:
    """% of account equity currently held in this ticker, or None if the
    execution service is unreachable - risk assessment must still work when it's
    down, just without portfolio-awareness (and it says so in a note)."""
    try:
        response = httpx.get(f"{settings.execution_service_url}/account", timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    account = response.json()
    equity = account.get("equity") or 0.0
    if equity <= 0:
        return 0.0

    for position in account.get("positions", []):
        if position.get("ticker", "").upper() == ticker.upper():
            market_value = abs(position.get("market_value") or 0.0)
            return market_value / equity * 100.0
    return 0.0


def assess_risk(
    research_job_id: UUID,
    ticker: str,
    quant_metrics: QuantMetrics,
    max_position_pct: float = DEFAULT_MAX_POSITION_PCT,
    target_vol_contribution_pct: float = DEFAULT_TARGET_VOL_CONTRIBUTION_PCT,
    stop_loss_vol_multiple: float = DEFAULT_STOP_LOSS_VOL_MULTIPLE,
    assumed_holding_days: int = DEFAULT_ASSUMED_HOLDING_DAYS,
    portfolio_max_position_pct: float = DEFAULT_PORTFOLIO_MAX_POSITION_PCT,
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

    existing_position_pct = _fetch_existing_position_pct(ticker)
    if existing_position_pct is None:
        notes.append(
            "execution service unreachable; sizing does not account for "
            "existing positions in this ticker"
        )
    else:
        available_room_pct = max(0.0, portfolio_max_position_pct - existing_position_pct)
        if suggested_position_size_pct > available_room_pct:
            notes.append(
                f"reduced from {suggested_position_size_pct:.2f}% to "
                f"{available_room_pct:.2f}% - existing position is already "
                f"{existing_position_pct:.2f}% of equity, against a "
                f"{portfolio_max_position_pct:.2f}% per-ticker concentration cap"
            )
            suggested_position_size_pct = available_room_pct

    return RiskAssessment(
        research_job_id=research_job_id,
        ticker=ticker.upper(),
        annualized_volatility=annualized_volatility,
        suggested_position_size_pct=suggested_position_size_pct,
        stop_loss_distance_pct=stop_loss_distance_pct,
        max_position_pct_cap=max_position_pct,
        target_position_volatility_contribution_pct=target_vol_contribution_pct,
        existing_position_pct=existing_position_pct,
        portfolio_max_position_pct_cap=portfolio_max_position_pct,
        notes=notes,
    )
