import re

from pydantic import BaseModel, field_validator

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
