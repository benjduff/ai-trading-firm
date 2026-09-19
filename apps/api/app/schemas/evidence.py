from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EvidenceSource(str, Enum):
    SEC_EDGAR = "sec_edgar"
    COMPANY_IR = "company_ir"
    EARNINGS_TRANSCRIPT = "earnings_transcript"
    FRED = "fred"
    MARKET_DATA = "market_data"
    NEWS = "news"
    OTHER = "other"


class Evidence(BaseModel):
    """claim -> source -> timestamp -> extracted evidence, with point-in-time integrity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    ticker: str
    source: EvidenceSource
    source_url: Optional[str] = None
    document_hash: str
    claim: str
    excerpt: str
    published_at: datetime
    ingested_at: datetime
    model_id: Optional[str] = None
    prompt_version: Optional[str] = None
