import re

from pydantic import BaseModel, field_validator

from app.schemas.human_decision import HumanDecisionAction

TICKER_PATTERN = re.compile(r"^[A-Z]{1,10}(\.[A-Z]{1,2})?$")


class CreateResearchRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("ticker must not be empty")
        if not TICKER_PATTERN.match(normalized):
            raise ValueError(
                "ticker must be 1-10 letters, optionally with a suffix like '.B'"
            )
        return normalized


class CreateHumanDecisionRequest(BaseModel):
    action: HumanDecisionAction
    reasoning: str
    decided_by: str

    @field_validator("reasoning")
    @classmethod
    def validate_reasoning(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("reasoning must not be empty")
        return stripped

    @field_validator("decided_by")
    @classmethod
    def validate_decided_by(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("decided_by must not be empty")
        return stripped
