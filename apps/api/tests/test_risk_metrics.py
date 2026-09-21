import numpy as np
import pytest

from app.quant import risk_metrics as rm


def test_daily_returns():
    closes = [100, 110, 90, 95, 80, 120]
    returns = rm.daily_returns(closes)
    np.testing.assert_allclose(
        returns,
        [10 / 100, -20 / 110, 5 / 90, -15 / 95, 40 / 80],
        rtol=1e-9,
    )


def test_daily_returns_too_short():
    assert rm.daily_returns([100]).size == 0
    assert rm.daily_returns([]).size == 0


def test_cumulative_return():
    closes = [100, 110, 90, 95, 80, 120]
    returns = rm.daily_returns(closes)
    assert rm.cumulative_return(returns) == pytest.approx(120 / 100 - 1, rel=1e-9)


def test_cumulative_return_empty():
    assert rm.cumulative_return([]) == 0.0


def test_annualized_volatility_zero_for_flat_returns():
    assert rm.annualized_volatility([0.01, 0.01, 0.01]) == 0.0


def test_annualized_volatility_too_short():
    assert rm.annualized_volatility([0.01]) == 0.0
    assert rm.annualized_volatility([]) == 0.0


def test_beta_matches_known_linear_relationship():
    # asset moves exactly 2x the benchmark with no idiosyncratic noise
    benchmark_returns = [0.01, -0.02, 0.03, 0.00, 0.015]
    asset_returns = [2 * r for r in benchmark_returns]
    assert rm.beta(asset_returns, benchmark_returns) == pytest.approx(2.0, rel=1e-9)


def test_beta_zero_benchmark_variance():
    assert rm.beta([0.01, 0.02], [0.0, 0.0]) == 0.0


def test_beta_too_short():
    assert rm.beta([0.01], [0.01]) == 0.0


def test_correlation_perfect_linear_relationship():
    benchmark_returns = [0.01, -0.02, 0.03, 0.00, 0.015]
    asset_returns = [2 * r for r in benchmark_returns]
    assert rm.correlation(asset_returns, benchmark_returns) == pytest.approx(1.0, rel=1e-9)


def test_correlation_zero_variance_series():
    assert rm.correlation([0.01, 0.01, 0.01], [0.02, -0.01, 0.03]) == 0.0


def test_max_drawdown_known_series():
    closes = [100, 110, 90, 95, 80, 120]
    # peak 110 -> trough 80 = -27.27%
    assert rm.max_drawdown(closes) == pytest.approx((80 - 110) / 110, rel=1e-9)


def test_max_drawdown_monotonic_up_is_zero():
    assert rm.max_drawdown([100, 110, 120, 130]) == pytest.approx(0.0, abs=1e-9)


def test_max_drawdown_too_short():
    assert rm.max_drawdown([100]) == 0.0


def test_abnormal_returns_zero_when_beta_perfectly_explains_moves():
    benchmark_returns = [0.01, -0.02, 0.03, 0.00, 0.015]
    asset_returns = [2 * r for r in benchmark_returns]
    b = rm.beta(asset_returns, benchmark_returns)
    abnormal = rm.abnormal_returns(asset_returns, benchmark_returns, b)
    np.testing.assert_allclose(abnormal, [0.0] * 5, atol=1e-9)


def test_abnormal_returns_nonzero_idiosyncratic_move():
    # asset has an extra +5% on top of a beta=1 relationship on the last day
    benchmark_returns = [0.01, 0.01, 0.01]
    asset_returns = [0.01, 0.01, 0.06]
    abnormal = rm.abnormal_returns(asset_returns, benchmark_returns, asset_beta=1.0)
    np.testing.assert_allclose(abnormal, [0.0, 0.0, 0.05], atol=1e-9)


def test_average_volume():
    assert rm.average_volume([1000, 2000, 3000]) == pytest.approx(2000.0)


def test_average_volume_empty():
    assert rm.average_volume([]) == 0.0
