from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.psychology import PsychologyReport


def _psychology_report_kwargs(**overrides):
    kwargs = dict(
        research_job_id=uuid4(),
        ticker="TEST",
        model_id="test-model",
        prompt_version="v1",
        summary="summary",
        market_temperature=0,
        expectation_gap="gap",
        fear_of_loss=0.5,
        fomo=0.5,
        narrative_saturation=0.5,
        crowding=0.5,
        dominant_narrative="narrative",
        differentiated_or_contrarian_view="view",
        psychology_confidence=0.5,
    )
    kwargs.update(overrides)
    return kwargs


@pytest.mark.parametrize("value", [-5, 0, 5])
def test_market_temperature_within_bounds_is_accepted(value):
    report = PsychologyReport(**_psychology_report_kwargs(market_temperature=value))
    assert report.market_temperature == value


@pytest.mark.parametrize("value", [-6, 6, 10, -100])
def test_market_temperature_out_of_bounds_is_rejected(value):
    with pytest.raises(ValidationError):
        PsychologyReport(**_psychology_report_kwargs(market_temperature=value))


@pytest.mark.parametrize("field", ["fear_of_loss", "fomo", "narrative_saturation", "crowding", "psychology_confidence"])
@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_unit_interval_fields_reject_out_of_range_values(field, value):
    with pytest.raises(ValidationError):
        PsychologyReport(**_psychology_report_kwargs(**{field: value}))


@pytest.mark.parametrize("field", ["fear_of_loss", "fomo", "narrative_saturation", "crowding", "psychology_confidence"])
def test_unit_interval_fields_accept_boundary_values(field):
    report = PsychologyReport(**_psychology_report_kwargs(**{field: 0.0}))
    assert getattr(report, field) == 0.0
    report = PsychologyReport(**_psychology_report_kwargs(**{field: 1.0}))
    assert getattr(report, field) == 1.0
