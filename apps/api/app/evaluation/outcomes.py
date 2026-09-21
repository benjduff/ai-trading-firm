from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from app.quant.market_data import fetch_daily_bars
from app.schemas.shadow_position import ShadowPosition
from app.schemas.trade_proposal import TradeAction

LOOKBACK_CALENDAR_DAYS_FOR_LATEST_PRICE = 10


def _latest_close(ticker: str) -> tuple:
    end = date.today()
    start = end - timedelta(days=LOOKBACK_CALENDAR_DAYS_FOR_LATEST_PRICE)
    bars = fetch_daily_bars(ticker, start, end)
    latest = bars[-1]
    return latest.close, latest.date


def freeze_proposal(
    research_job_id: UUID, trade_proposal_id: UUID, ticker: str, action: TradeAction
) -> ShadowPosition:
    entry_price, entry_price_as_of = _latest_close(ticker)
    return ShadowPosition(
        research_job_id=research_job_id,
        trade_proposal_id=trade_proposal_id,
        ticker=ticker,
        action=action,
        entry_price=entry_price,
        entry_price_as_of=entry_price_as_of,
    )


@dataclass
class ShadowPerformance:
    shadow_position: ShadowPosition
    current_price: float
    current_price_as_of: date
    days_since_frozen: int
    raw_price_return_pct: float
    shadow_return_pct: float


def evaluate_shadow_position(shadow: ShadowPosition) -> ShadowPerformance:
    current_price, current_price_as_of = _latest_close(shadow.ticker)
    raw_return = current_price / shadow.entry_price - 1.0

    if shadow.action == TradeAction.BUY:
        shadow_return = raw_return
    elif shadow.action == TradeAction.SELL:
        shadow_return = -raw_return
    else:
        shadow_return = 0.0

    return ShadowPerformance(
        shadow_position=shadow,
        current_price=current_price,
        current_price_as_of=current_price_as_of,
        days_since_frozen=(current_price_as_of - shadow.entry_price_as_of).days,
        raw_price_return_pct=raw_return,
        shadow_return_pct=shadow_return,
    )
