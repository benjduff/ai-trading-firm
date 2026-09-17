from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ResearchJobStatus(str, Enum):
    PENDING = "pending"


class ResearchJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    ticker: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ResearchJobStatus = ResearchJobStatus.PENDING
    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requested_by: Optional[str] = None
