"""Deterministic quant calculations. No LLM involved anywhere in this module,
per CLAUDE.md's non-negotiable rule: LLMs interpret, deterministic Python calculates."""

import numpy as np

TRADING_DAYS_PER_YEAR = 252


def daily_returns(closes) -> np.ndarray:
    closes = np.asarray(closes, dtype=float)
    if len(closes) < 2:
        return np.array([])
    return closes[1:] / closes[:-1] - 1.0


def cumulative_return(returns) -> float:
    returns = np.asarray(returns, dtype=float)
    if len(returns) == 0:
        return 0.0
    return float(np.prod(1.0 + returns) - 1.0)


def annualized_volatility(returns) -> float:
    returns = np.asarray(returns, dtype=float)
    if len(returns) < 2:
        return 0.0
    return float(np.std(returns, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def beta(asset_returns, benchmark_returns) -> float:
    asset_returns = np.asarray(asset_returns, dtype=float)
    benchmark_returns = np.asarray(benchmark_returns, dtype=float)
    n = min(len(asset_returns), len(benchmark_returns))
    if n < 2:
        return 0.0
    asset_returns, benchmark_returns = asset_returns[-n:], benchmark_returns[-n:]
    benchmark_var = np.var(benchmark_returns, ddof=1)
    if benchmark_var == 0:
        return 0.0
    covariance = np.cov(asset_returns, benchmark_returns, ddof=1)[0, 1]
    return float(covariance / benchmark_var)


def correlation(asset_returns, benchmark_returns) -> float:
    asset_returns = np.asarray(asset_returns, dtype=float)
    benchmark_returns = np.asarray(benchmark_returns, dtype=float)
    n = min(len(asset_returns), len(benchmark_returns))
    if n < 2:
        return 0.0
    asset_returns, benchmark_returns = asset_returns[-n:], benchmark_returns[-n:]
    if np.std(asset_returns) == 0 or np.std(benchmark_returns) == 0:
        return 0.0
    return float(np.corrcoef(asset_returns, benchmark_returns)[0, 1])


def max_drawdown(closes) -> float:
    closes = np.asarray(closes, dtype=float)
    if len(closes) < 2:
        return 0.0
    running_max = np.maximum.accumulate(closes)
    drawdowns = closes / running_max - 1.0
    return float(np.min(drawdowns))


def abnormal_returns(asset_returns, benchmark_returns, asset_beta: float) -> np.ndarray:
    """Market-model abnormal return: actual return minus beta * benchmark return."""
    asset_returns = np.asarray(asset_returns, dtype=float)
    benchmark_returns = np.asarray(benchmark_returns, dtype=float)
    n = min(len(asset_returns), len(benchmark_returns))
    asset_returns, benchmark_returns = asset_returns[-n:], benchmark_returns[-n:]
    expected_returns = asset_beta * benchmark_returns
    return asset_returns - expected_returns


def average_volume(volumes) -> float:
    volumes = np.asarray(volumes, dtype=float)
    if len(volumes) == 0:
        return 0.0
    return float(np.mean(volumes))
