from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from app.quant import risk_metrics
from app.quant.market_data import MarketDataError, fetch_daily_bars
from app.schemas.quant import QuantMetrics

DEFAULT_BENCHMARK_TICKER = "SPY"
CALENDAR_DAYS_PER_TRADING_DAY = 1.6


def _align_by_date(bars_a: list, bars_b: list):
    by_date_a = {b.date: b for b in bars_a}
    by_date_b = {b.date: b for b in bars_b}
    common_dates = sorted(set(by_date_a) & set(by_date_b))
    return [by_date_a[d] for d in common_dates], [by_date_b[d] for d in common_dates]


def run_quant_analysis(
    research_job_id: UUID,
    ticker: str,
    lookback_days: int = 252,
    benchmark_ticker: str = DEFAULT_BENCHMARK_TICKER,
    sector_ticker: Optional[str] = None,
) -> QuantMetrics:
    end = date.today()
    start = end - timedelta(days=int(lookback_days * CALENDAR_DAYS_PER_TRADING_DAY) + 10)

    asset_bars = fetch_daily_bars(ticker, start, end)
    benchmark_bars = fetch_daily_bars(benchmark_ticker, start, end)
    asset_bars, benchmark_bars = _align_by_date(asset_bars, benchmark_bars)

    if len(asset_bars) < 2:
        raise MarketDataError(f"not enough aligned price history for {ticker}")

    asset_closes = [b.close for b in asset_bars]
    benchmark_closes = [b.close for b in benchmark_bars]
    asset_volumes = [b.volume for b in asset_bars]

    asset_returns = risk_metrics.daily_returns(asset_closes)
    benchmark_returns = risk_metrics.daily_returns(benchmark_closes)

    asset_beta = risk_metrics.beta(asset_returns, benchmark_returns)
    abnormal = risk_metrics.abnormal_returns(asset_returns, benchmark_returns, asset_beta)

    sector_relative_return = None
    if sector_ticker:
        sector_bars = fetch_daily_bars(sector_ticker, start, end)
        aligned_asset_bars, aligned_sector_bars = _align_by_date(asset_bars, sector_bars)
        if len(aligned_asset_bars) >= 2:
            asset_returns_vs_sector = risk_metrics.daily_returns(
                [b.close for b in aligned_asset_bars]
            )
            sector_returns = risk_metrics.daily_returns(
                [b.close for b in aligned_sector_bars]
            )
            sector_relative_return = risk_metrics.cumulative_return(
                asset_returns_vs_sector
            ) - risk_metrics.cumulative_return(sector_returns)

    return QuantMetrics(
        research_job_id=research_job_id,
        ticker=ticker.upper(),
        benchmark_ticker=benchmark_ticker.upper(),
        sector_ticker=sector_ticker.upper() if sector_ticker else None,
        lookback_trading_days=len(asset_returns),
        as_of=asset_bars[-1].date,
        cumulative_return=risk_metrics.cumulative_return(asset_returns),
        annualized_volatility=risk_metrics.annualized_volatility(asset_returns),
        beta=asset_beta,
        correlation_to_benchmark=risk_metrics.correlation(asset_returns, benchmark_returns),
        max_drawdown=risk_metrics.max_drawdown(asset_closes),
        cumulative_abnormal_return=float(sum(abnormal)),
        average_daily_volume=risk_metrics.average_volume(asset_volumes),
        sector_relative_return=sector_relative_return,
    )
