import pytest
from pydantic import ValidationError

from app.requests import CreateHumanDecisionRequest, CreateResearchRequest


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("oxy", "OXY"),
        ("  oxy  ", "OXY"),
        ("BRK.B", "BRK.B"),
        ("brk.b", "BRK.B"),
        ("a", "A"),
    ],
)
def test_ticker_is_normalized_to_uppercase(raw, expected):
    assert CreateResearchRequest(ticker=raw).ticker == expected


@pytest.mark.parametrize("raw", ["", "   ", "toolongtickerxx", "12345", "OXY!", "OX Y"])
def test_invalid_ticker_is_rejected(raw):
    with pytest.raises(ValidationError):
        CreateResearchRequest(ticker=raw)


def test_decision_request_normalizes_reasoning_and_decided_by():
    request = CreateHumanDecisionRequest(
        action="approve", reasoning="  looks good  ", decided_by="  ben  "
    )
    assert request.reasoning == "looks good"
    assert request.decided_by == "ben"


@pytest.mark.parametrize("reasoning", ["", "   "])
def test_decision_request_rejects_empty_reasoning(reasoning):
    with pytest.raises(ValidationError):
        CreateHumanDecisionRequest(action="approve", reasoning=reasoning, decided_by="ben")


@pytest.mark.parametrize("decided_by", ["", "   "])
def test_decision_request_rejects_empty_decided_by(decided_by):
    with pytest.raises(ValidationError):
        CreateHumanDecisionRequest(action="approve", reasoning="ok", decided_by=decided_by)


def test_decision_request_rejects_invalid_action():
    with pytest.raises(ValidationError):
        CreateHumanDecisionRequest(action="maybe", reasoning="ok", decided_by="ben")
