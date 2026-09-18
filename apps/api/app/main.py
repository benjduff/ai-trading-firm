from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db import get_db
from app.db_models import ResearchJobRecord
from app.requests import CreateResearchRequest
from app.schemas import ResearchJob

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
