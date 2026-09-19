from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db import get_db
from app.db_models import EvidenceRecord, ResearchJobRecord
from app.ingestion.sec_edgar import TickerNotFoundError, fetch_filing_evidence
from app.requests import CreateResearchRequest
from app.schemas import Evidence, ResearchJob
from app.schemas.research_job import ResearchJobStatus

app = FastAPI(
    title="AI Trading Firm API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai-trading-firm-api",
    }


@app.post("/research", status_code=201)
async def create_research(
    request: CreateResearchRequest, db: Session = Depends(get_db)
) -> ResearchJob:
    record = ResearchJobRecord(ticker=request.ticker)
    db.add(record)
    db.commit()
    db.refresh(record)
    return ResearchJob.model_validate(record)


@app.get("/research/{job_id}")
async def get_research(job_id: UUID, db: Session = Depends(get_db)) -> ResearchJob:
    record = db.get(ResearchJobRecord, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="research job not found")
    return ResearchJob.model_validate(record)


def _get_job_or_404(job_id: UUID, db: Session) -> ResearchJobRecord:
    record = db.get(ResearchJobRecord, job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="research job not found")
    return record


@app.post("/research/{job_id}/ingest/sec-edgar", status_code=201)
def ingest_sec_edgar(job_id: UUID, db: Session = Depends(get_db)) -> list[Evidence]:
    job = _get_job_or_404(job_id, db)

    try:
        fetched = fetch_filing_evidence(job.ticker)
    except TickerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502, detail=f"SEC EDGAR request failed: {e}"
        )

    existing_urls = {
        row.source_url
        for row in db.query(EvidenceRecord.source_url).filter(
            EvidenceRecord.ticker == job.ticker
        )
    }

    new_records = [
        EvidenceRecord(**evidence.model_dump(exclude={"id"}))
        for evidence in fetched
        if evidence.source_url not in existing_urls
    ]
    db.add_all(new_records)

    job.status = ResearchJobStatus.EVIDENCE_INGESTED.value
    db.add(job)
    db.commit()

    stored = (
        db.query(EvidenceRecord).filter(EvidenceRecord.ticker == job.ticker).all()
    )
    return [Evidence.model_validate(row) for row in stored]


@app.get("/research/{job_id}/evidence")
async def list_research_evidence(
    job_id: UUID, db: Session = Depends(get_db)
) -> list[Evidence]:
    job = _get_job_or_404(job_id, db)
    rows = db.query(EvidenceRecord).filter(EvidenceRecord.ticker == job.ticker).all()
    return [Evidence.model_validate(row) for row in rows]
