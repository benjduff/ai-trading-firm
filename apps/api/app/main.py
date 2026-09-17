from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import CreateResearchRequest, ResearchJob

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

research_jobs: dict[UUID, ResearchJob] = {}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai-trading-firm-api",
    }


@app.post("/research", status_code=201)
async def create_research(request: CreateResearchRequest) -> ResearchJob:
    job = ResearchJob(ticker=request.ticker)
    research_jobs[job.id] = job
    return job


@app.get("/research/{job_id}")
async def get_research(job_id: UUID) -> ResearchJob:
    job = research_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="research job not found")
    return job
