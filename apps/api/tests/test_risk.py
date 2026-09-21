from datetime import date
from uuid import uuid4

import pytest

from app.quant import risk
from app.schemas.quant import QuantMetrics


def _quant_metrics(**overrides) -> QuantMetrics:
    defaults = dict(
        research_job_id=uuid4(),
        ticker="TEST",
        benchmark_ticker="SPY",
        lookback_trading_days=252,
        as_of=date.today(),
        cumulative_return=0.1,
        annualized_volatility=0.20,
        beta=1.0,
        correlation_to_benchmark=0.5,
        max_drawdown=-0.15,
        cumulative_abnormal_return=0.02,
        average_daily_volume=1_000_000,
    )
    defaults.update(overrides)
    return QuantMetrics(**defaults)


@pytest.fixture(autouse=True)
def no_portfolio_call(monkeypatch):
    """Unless a test overrides it, pretend the ticker has no existing position -
    keeps every test isolated from the network/execution service by default."""
    monkeypatch.setattr(risk, "_fetch_existing_position_pct", lambda ticker: 0.0)


def test_position_size_scales_inversely_with_volatility():
    low_vol = risk.assess_risk(uuid4(), "TEST", _quant_metrics(annualized_volatility=0.20))
    high_vol = risk.assess_risk(uuid4(), "TEST", _quant_metrics(annualized_volatility=0.40))

    # 1.0% target / 0.20 = 5.0%, capped at the 5.0% default max -> at the cap
    assert low_vol.suggested_position_size_pct == pytest.approx(5.0)
    # 1.0% target / 0.40 = 2.5%, below the cap
    assert high_vol.suggested_position_size_pct == pytest.approx(2.5)


def test_position_size_falls_back_to_cap_when_volatility_is_zero():
    result = risk.assess_risk(uuid4(), "TEST", _quant_metrics(annualized_volatility=0.0))
    assert result.suggested_position_size_pct == pytest.approx(risk.DEFAULT_MAX_POSITION_PCT)
    assert any("volatility was zero" in note for note in result.notes)


def test_high_drawdown_adds_a_note():
    result = risk.assess_risk(uuid4(), "TEST", _quant_metrics(max_drawdown=-0.45))
    assert any("max drawdown" in note for note in result.notes)


def test_low_drawdown_adds_no_note():
    result = risk.assess_risk(uuid4(), "TEST", _quant_metrics(max_drawdown=-0.05))
    assert not any("max drawdown" in note for note in result.notes)


def test_stop_loss_distance_scales_with_volatility():
    low_vol = risk.assess_risk(uuid4(), "TEST", _quant_metrics(annualized_volatility=0.20))
    high_vol = risk.assess_risk(uuid4(), "TEST", _quant_metrics(annualized_volatility=0.40))
    assert high_vol.stop_loss_distance_pct > low_vol.stop_loss_distance_pct


def test_portfolio_concentration_cap_reduces_sizing(monkeypatch):
    # existing position is already 8% of equity, against a 10% concentration cap,
    # while volatility alone would want the full 5% max single-trade size
    monkeypatch.setattr(risk, "_fetch_existing_position_pct", lambda ticker: 8.0)

    result = risk.assess_risk(
        uuid4(), "TEST", _quant_metrics(annualized_volatility=0.05)
    )

    assert result.existing_position_pct == pytest.approx(8.0)
    assert result.suggested_position_size_pct == pytest.approx(2.0)
    assert any("concentration cap" in note for note in result.notes)


def test_portfolio_concentration_cap_not_triggered_when_room_available(monkeypatch):
    monkeypatch.setattr(risk, "_fetch_existing_position_pct", lambda ticker: 1.0)

    result = risk.assess_risk(uuid4(), "TEST", _quant_metrics(annualized_volatility=0.20))

    assert result.existing_position_pct == pytest.approx(1.0)
    assert result.suggested_position_size_pct == pytest.approx(5.0)
    assert not any("concentration cap" in note for note in result.notes)


def test_execution_service_unreachable_degrades_gracefully(monkeypatch):
    monkeypatch.setattr(risk, "_fetch_existing_position_pct", lambda ticker: None)

    result = risk.assess_risk(uuid4(), "TEST", _quant_metrics())

    assert result.existing_position_pct is None
    # sizing proceeds using only volatility, unmodified by portfolio state
    assert result.suggested_position_size_pct == pytest.approx(5.0)
    assert any("execution service unreachable" in note for note in result.notes)


def test_ticker_is_uppercased():
    result = risk.assess_risk(uuid4(), "test", _quant_metrics(ticker="test"))
    assert result.ticker == "TEST"
