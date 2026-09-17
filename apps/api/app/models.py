import re
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

TICKER_PATTERN = re.compile(r"^[A-Z]{1,10}(\.[A-Z]{1,2})?$")


class ResearchJobStatus(str, Enum):
    PENDING = "pending"


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


class ResearchJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    ticker: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ResearchJobStatus = ResearchJobStatus.PENDING
    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requested_by: Optional[str] = None
