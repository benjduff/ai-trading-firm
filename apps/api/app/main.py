from typing import Optional
from uuid import UUID

import httpx
import openai
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.agents.cio import run_cio_synthesis
from app.agents.fundamental import run_fundamental_analysis
from app.agents.psychology import run_psychology_analysis
from app.agents.red_team import run_red_team_analysis
from app.db import get_db
from app.db_models import (
    EvidenceRecord,
    FundamentalReportRecord,
    HumanDecisionRecord,
    PsychologyReportRecord,
    QuantMetricsRecord,
    RedTeamReportRecord,
    ResearchJobRecord,
    RiskAssessmentRecord,
    ShadowPositionRecord,
    TradeProposalRecord,
)
from app.config import settings
from app.evaluation.outcomes import evaluate_shadow_position, freeze_proposal
from app.ingestion.sec_edgar import TickerNotFoundError, fetch_filing_evidence
from app.llm import (
    ModelGatewayNotConfiguredError,
    get_default_gateway,
    get_red_team_gateway,
)
from app.quant.analysis import DEFAULT_BENCHMARK_TICKER, run_quant_analysis
from app.quant.market_data import MarketDataError
from app.quant.risk import assess_risk
from app.requests import CreateHumanDecisionRequest, CreateResearchRequest
from app.schemas import (
    AccountSummary,
    Evidence,
    ExecutedOrder,
    FundamentalReport,
    HumanDecision,
    PsychologyReport,
    QuantMetrics,
    RedTeamReport,
    ResearchJob,
    ResearchSummary,
    RiskAssessment,
    ShadowPerformanceResponse,
    ShadowPosition,
    TradeProposal,
)
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


def _get_evidence_or_400(ticker: str, db: Session) -> list[Evidence]:
    rows = db.query(EvidenceRecord).filter(EvidenceRecord.ticker == ticker).all()
    if not rows:
        raise HTTPException(
            status_code=400,
            detail="no evidence for this ticker yet; ingest evidence first",
        )
    return [Evidence.model_validate(row) for row in rows]


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


@app.post("/research/{job_id}/analyze/fundamental", status_code=201)
def analyze_fundamental(
    job_id: UUID, db: Session = Depends(get_db)
) -> FundamentalReport:
    job = _get_job_or_404(job_id, db)
    evidence = _get_evidence_or_400(job.ticker, db)

    try:
        gateway = get_default_gateway()
    except ModelGatewayNotConfiguredError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        report = run_fundamental_analysis(gateway, job.id, job.ticker, evidence)
    except openai.OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    record = FundamentalReportRecord(
        **report.model_dump(exclude={"agent_type"}),
        agent_type=report.agent_type.value,
    )
    db.add(record)

    job.status = ResearchJobStatus.FUNDAMENTAL_ANALYSIS_COMPLETE.value
    db.add(job)
    db.commit()
    db.refresh(record)

    return FundamentalReport.model_validate(record)


@app.get("/research/{job_id}/fundamental-report")
async def get_fundamental_report(
    job_id: UUID, db: Session = Depends(get_db)
) -> list[FundamentalReport]:
    _get_job_or_404(job_id, db)
    rows = (
        db.query(FundamentalReportRecord)
        .filter(FundamentalReportRecord.research_job_id == job_id)
        .order_by(FundamentalReportRecord.created_at.desc())
        .all()
    )
    return [FundamentalReport.model_validate(row) for row in rows]


@app.post("/research/{job_id}/analyze/psychology", status_code=201)
def analyze_psychology(
    job_id: UUID, db: Session = Depends(get_db)
) -> PsychologyReport:
    job = _get_job_or_404(job_id, db)
    evidence = _get_evidence_or_400(job.ticker, db)

    try:
        gateway = get_default_gateway()
    except ModelGatewayNotConfiguredError as e:
        raise HTTPException(status_code=500, detail=str(e))

    previous_state = (
        db.query(PsychologyReportRecord)
        .filter(PsychologyReportRecord.ticker == job.ticker)
        .order_by(PsychologyReportRecord.created_at.desc())
        .first()
    )
    previous_state_id = previous_state.id if previous_state else None

    try:
        report = run_psychology_analysis(
            gateway, job.id, job.ticker, evidence, previous_state_id
        )
    except openai.OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    record = PsychologyReportRecord(
        **report.model_dump(exclude={"agent_type"}),
        agent_type=report.agent_type.value,
    )
    db.add(record)

    job.status = ResearchJobStatus.PSYCHOLOGY_ANALYSIS_COMPLETE.value
    db.add(job)
    db.commit()
    db.refresh(record)

    return PsychologyReport.model_validate(record)


@app.get("/research/{job_id}/psychology-report")
async def get_psychology_report(
    job_id: UUID, db: Session = Depends(get_db)
) -> list[PsychologyReport]:
    _get_job_or_404(job_id, db)
    rows = (
        db.query(PsychologyReportRecord)
        .filter(PsychologyReportRecord.research_job_id == job_id)
        .order_by(PsychologyReportRecord.created_at.desc())
        .all()
    )
    return [PsychologyReport.model_validate(row) for row in rows]


def _format_fundamental_thesis(report: FundamentalReportRecord) -> str:
    return "\n".join(
        [
            f"Summary: {report.summary}",
            "Key findings: " + "; ".join(report.key_findings),
            f"Financial health: {report.financial_health}",
            f"Valuation view: {report.valuation_view}",
            "Catalysts: " + "; ".join(report.catalysts),
            "Risks already noted: " + "; ".join(report.risks),
        ]
    )


@app.post("/research/{job_id}/analyze/red-team", status_code=201)
def analyze_red_team(job_id: UUID, db: Session = Depends(get_db)) -> RedTeamReport:
    job = _get_job_or_404(job_id, db)
    evidence = _get_evidence_or_400(job.ticker, db)

    fundamental = (
        db.query(FundamentalReportRecord)
        .filter(FundamentalReportRecord.research_job_id == job_id)
        .order_by(FundamentalReportRecord.created_at.desc())
        .first()
    )
    if fundamental is None:
        raise HTTPException(
            status_code=400,
            detail="no fundamental report for this job yet; run fundamental analysis first",
        )

    try:
        gateway = get_red_team_gateway()
    except ModelGatewayNotConfiguredError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        report = run_red_team_analysis(
            gateway,
            job.id,
            job.ticker,
            evidence,
            _format_fundamental_thesis(fundamental),
        )
    except openai.OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    record = RedTeamReportRecord(
        **report.model_dump(exclude={"agent_type"}),
        agent_type=report.agent_type.value,
    )
    db.add(record)

    job.status = ResearchJobStatus.RED_TEAM_ANALYSIS_COMPLETE.value
    db.add(job)
    db.commit()
    db.refresh(record)

    return RedTeamReport.model_validate(record)


@app.get("/research/{job_id}/red-team-report")
async def get_red_team_report(
    job_id: UUID, db: Session = Depends(get_db)
) -> list[RedTeamReport]:
    _get_job_or_404(job_id, db)
    rows = (
        db.query(RedTeamReportRecord)
        .filter(RedTeamReportRecord.research_job_id == job_id)
        .order_by(RedTeamReportRecord.created_at.desc())
        .all()
    )
    return [RedTeamReport.model_validate(row) for row in rows]


@app.post("/research/{job_id}/analyze/quant", status_code=201)
def analyze_quant(
    job_id: UUID,
    benchmark_ticker: str = DEFAULT_BENCHMARK_TICKER,
    sector_ticker: Optional[str] = None,
    lookback_days: int = 252,
    db: Session = Depends(get_db),
) -> QuantMetrics:
    job = _get_job_or_404(job_id, db)

    try:
        metrics = run_quant_analysis(
            job.id,
            job.ticker,
            lookback_days=lookback_days,
            benchmark_ticker=benchmark_ticker,
            sector_ticker=sector_ticker,
        )
    except MarketDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"market data request failed: {e}")

    record = QuantMetricsRecord(**metrics.model_dump())
    db.add(record)

    job.status = ResearchJobStatus.QUANT_ANALYSIS_COMPLETE.value
    db.add(job)
    db.commit()
    db.refresh(record)

    return QuantMetrics.model_validate(record)


@app.get("/research/{job_id}/quant-metrics")
async def get_quant_metrics(
    job_id: UUID, db: Session = Depends(get_db)
) -> list[QuantMetrics]:
    _get_job_or_404(job_id, db)
    rows = (
        db.query(QuantMetricsRecord)
        .filter(QuantMetricsRecord.research_job_id == job_id)
        .order_by(QuantMetricsRecord.computed_at.desc())
        .all()
    )
    return [QuantMetrics.model_validate(row) for row in rows]


@app.post("/research/{job_id}/analyze/risk", status_code=201)
def analyze_risk(job_id: UUID, db: Session = Depends(get_db)) -> RiskAssessment:
    job = _get_job_or_404(job_id, db)

    quant_row = (
        db.query(QuantMetricsRecord)
        .filter(QuantMetricsRecord.research_job_id == job_id)
        .order_by(QuantMetricsRecord.computed_at.desc())
        .first()
    )
    if quant_row is None:
        raise HTTPException(
            status_code=400,
            detail="no quant metrics for this job yet; run quant analysis first",
        )
    quant_metrics = QuantMetrics.model_validate(quant_row)

    assessment = assess_risk(job.id, job.ticker, quant_metrics)

    record = RiskAssessmentRecord(**assessment.model_dump())
    db.add(record)

    job.status = ResearchJobStatus.RISK_ASSESSMENT_COMPLETE.value
    db.add(job)
    db.commit()
    db.refresh(record)

    return RiskAssessment.model_validate(record)


@app.get("/research/{job_id}/risk-assessment")
async def get_risk_assessment(
    job_id: UUID, db: Session = Depends(get_db)
) -> list[RiskAssessment]:
    _get_job_or_404(job_id, db)
    rows = (
        db.query(RiskAssessmentRecord)
        .filter(RiskAssessmentRecord.research_job_id == job_id)
        .order_by(RiskAssessmentRecord.computed_at.desc())
        .all()
    )
    return [RiskAssessment.model_validate(row) for row in rows]


@app.post("/research/{job_id}/synthesize", status_code=201)
def synthesize_trade_proposal(
    job_id: UUID, db: Session = Depends(get_db)
) -> TradeProposal:
    job = _get_job_or_404(job_id, db)

    def _latest(model, timestamp_column, label: str):
        row = (
            db.query(model)
            .filter(model.research_job_id == job_id)
            .order_by(timestamp_column.desc())
            .first()
        )
        return row, label

    lookups = [
        _latest(FundamentalReportRecord, FundamentalReportRecord.created_at, "fundamental"),
        _latest(PsychologyReportRecord, PsychologyReportRecord.created_at, "psychology"),
        _latest(RedTeamReportRecord, RedTeamReportRecord.created_at, "red_team"),
        _latest(QuantMetricsRecord, QuantMetricsRecord.computed_at, "quant"),
        _latest(RiskAssessmentRecord, RiskAssessmentRecord.computed_at, "risk"),
    ]
    missing = [label for row, label in lookups if row is None]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"missing analysis for: {', '.join(missing)}; run those first",
        )
    fundamental_row, psychology_row, red_team_row, quant_row, risk_row = (
        row for row, _ in lookups
    )

    try:
        gateway = get_default_gateway()
    except ModelGatewayNotConfiguredError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        proposal = run_cio_synthesis(
            gateway,
            job.id,
            job.ticker,
            FundamentalReport.model_validate(fundamental_row),
            PsychologyReport.model_validate(psychology_row),
            RedTeamReport.model_validate(red_team_row),
            QuantMetrics.model_validate(quant_row),
            RiskAssessment.model_validate(risk_row),
        )
    except openai.OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {e}")

    record = TradeProposalRecord(
        **proposal.model_dump(exclude={"action"}),
        action=proposal.action.value,
    )
    db.add(record)

    # Freeze unconditionally, before any human decision exists - this is what lets
    # the firm grade its own calls (including rejected ones) against reality.
    try:
        shadow = freeze_proposal(job.id, proposal.id, job.ticker, proposal.action)
    except MarketDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"market data request failed: {e}")
    db.add(ShadowPositionRecord(**shadow.model_dump(exclude={"action"}), action=shadow.action.value))

    job.status = ResearchJobStatus.TRADE_PROPOSAL_COMPLETE.value
    db.add(job)
    db.commit()
    db.refresh(record)

    return TradeProposal.model_validate(record)


@app.get("/research/{job_id}/trade-proposal")
async def get_trade_proposal(
    job_id: UUID, db: Session = Depends(get_db)
) -> list[TradeProposal]:
    _get_job_or_404(job_id, db)
    rows = (
        db.query(TradeProposalRecord)
        .filter(TradeProposalRecord.research_job_id == job_id)
        .order_by(TradeProposalRecord.created_at.desc())
        .all()
    )
    return [TradeProposal.model_validate(row) for row in rows]


@app.get("/research/{job_id}/summary")
async def get_research_summary(
    job_id: UUID, db: Session = Depends(get_db)
) -> ResearchSummary:
    job = _get_job_or_404(job_id, db)

    def _latest(model, timestamp_column):
        return (
            db.query(model)
            .filter(model.research_job_id == job_id)
            .order_by(timestamp_column.desc())
            .first()
        )

    evidence_rows = (
        db.query(EvidenceRecord).filter(EvidenceRecord.ticker == job.ticker).all()
    )
    fundamental_row = _latest(FundamentalReportRecord, FundamentalReportRecord.created_at)
    psychology_row = _latest(PsychologyReportRecord, PsychologyReportRecord.created_at)
    red_team_row = _latest(RedTeamReportRecord, RedTeamReportRecord.created_at)
    quant_row = _latest(QuantMetricsRecord, QuantMetricsRecord.computed_at)
    risk_row = _latest(RiskAssessmentRecord, RiskAssessmentRecord.computed_at)
    trade_proposal_row = _latest(TradeProposalRecord, TradeProposalRecord.created_at)
    decision_row = _latest(HumanDecisionRecord, HumanDecisionRecord.decided_at)

    return ResearchSummary(
        job=ResearchJob.model_validate(job),
        evidence=[Evidence.model_validate(row) for row in evidence_rows],
        fundamental_report=FundamentalReport.model_validate(fundamental_row)
        if fundamental_row
        else None,
        psychology_report=PsychologyReport.model_validate(psychology_row)
        if psychology_row
        else None,
        red_team_report=RedTeamReport.model_validate(red_team_row) if red_team_row else None,
        quant_metrics=QuantMetrics.model_validate(quant_row) if quant_row else None,
        risk_assessment=RiskAssessment.model_validate(risk_row) if risk_row else None,
        trade_proposal=TradeProposal.model_validate(trade_proposal_row)
        if trade_proposal_row
        else None,
        human_decision=HumanDecision.model_validate(decision_row) if decision_row else None,
    )


@app.post("/research/{job_id}/decision", status_code=201)
def record_human_decision(
    job_id: UUID, request: CreateHumanDecisionRequest, db: Session = Depends(get_db)
) -> HumanDecision:
    job = _get_job_or_404(job_id, db)

    trade_proposal_row = (
        db.query(TradeProposalRecord)
        .filter(TradeProposalRecord.research_job_id == job_id)
        .order_by(TradeProposalRecord.created_at.desc())
        .first()
    )
    if trade_proposal_row is None:
        raise HTTPException(
            status_code=400,
            detail="no trade proposal for this job yet; synthesize one first",
        )

    record = HumanDecisionRecord(
        research_job_id=job.id,
        trade_proposal_id=trade_proposal_row.id,
        action=request.action.value,
        reasoning=request.reasoning,
        decided_by=request.decided_by,
    )
    db.add(record)

    job.status = ResearchJobStatus.HUMAN_DECISION_RECORDED.value
    db.add(job)
    db.commit()
    db.refresh(record)

    return HumanDecision.model_validate(record)


@app.get("/research/{job_id}/decision")
async def list_human_decisions(
    job_id: UUID, db: Session = Depends(get_db)
) -> list[HumanDecision]:
    _get_job_or_404(job_id, db)
    rows = (
        db.query(HumanDecisionRecord)
        .filter(HumanDecisionRecord.research_job_id == job_id)
        .order_by(HumanDecisionRecord.decided_at.desc())
        .all()
    )
    return [HumanDecision.model_validate(row) for row in rows]


@app.get("/research/{job_id}/shadow-performance")
def get_shadow_performance(
    job_id: UUID, db: Session = Depends(get_db)
) -> ShadowPerformanceResponse:
    _get_job_or_404(job_id, db)

    shadow_row = (
        db.query(ShadowPositionRecord)
        .filter(ShadowPositionRecord.research_job_id == job_id)
        .order_by(ShadowPositionRecord.frozen_at.desc())
        .first()
    )
    if shadow_row is None:
        raise HTTPException(
            status_code=400,
            detail="no frozen shadow position for this job yet; synthesize a trade proposal first",
        )
    shadow = ShadowPosition.model_validate(shadow_row)

    try:
        performance = evaluate_shadow_position(shadow)
    except MarketDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"market data request failed: {e}")

    decision_row = (
        db.query(HumanDecisionRecord)
        .filter(HumanDecisionRecord.research_job_id == job_id)
        .order_by(HumanDecisionRecord.decided_at.desc())
        .first()
    )

    return ShadowPerformanceResponse(
        shadow_position=shadow,
        current_price=performance.current_price,
        current_price_as_of=performance.current_price_as_of,
        days_since_frozen=performance.days_since_frozen,
        raw_price_return_pct=performance.raw_price_return_pct,
        shadow_return_pct=performance.shadow_return_pct,
        human_decision_action=decision_row.action if decision_row else None,
    )


def _latest_trade_proposal(job_id: UUID, db: Session) -> TradeProposalRecord:
    proposal = (
        db.query(TradeProposalRecord)
        .filter(TradeProposalRecord.research_job_id == job_id)
        .order_by(TradeProposalRecord.created_at.desc())
        .first()
    )
    if proposal is None:
        raise HTTPException(
            status_code=400, detail="no trade proposal for this job yet"
        )
    return proposal


@app.post("/research/{job_id}/execute", status_code=201)
def execute_trade(job_id: UUID, db: Session = Depends(get_db)) -> ExecutedOrder:
    """Proxies a human-triggered request to the separate execution service. This
    app never talks to a broker itself - it only forwards the click, and the
    execution service independently re-verifies an approved decision exists
    before doing anything. See apps/execution for why that separation matters."""
    job = _get_job_or_404(job_id, db)
    proposal = _latest_trade_proposal(job_id, db)

    decision = (
        db.query(HumanDecisionRecord)
        .filter(HumanDecisionRecord.research_job_id == job_id)
        .order_by(HumanDecisionRecord.decided_at.desc())
        .first()
    )
    if decision is None or decision.action != "approve":
        raise HTTPException(
            status_code=400,
            detail="no approved human decision for this job; approve the proposal first",
        )

    try:
        response = httpx.post(
            f"{settings.execution_service_url}/execute",
            json={"trade_proposal_id": str(proposal.id)},
            timeout=30.0,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"execution service unreachable: {e}")

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", response.text),
        )

    job.status = ResearchJobStatus.ORDER_EXECUTED.value
    db.add(job)
    db.commit()

    return ExecutedOrder.model_validate(response.json())


@app.get("/research/{job_id}/order")
def get_order(job_id: UUID, db: Session = Depends(get_db)) -> ExecutedOrder:
    proposal = _latest_trade_proposal(job_id, db)

    try:
        response = httpx.get(
            f"{settings.execution_service_url}/orders/{proposal.id}", timeout=10.0
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"execution service unreachable: {e}")

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", response.text),
        )

    return ExecutedOrder.model_validate(response.json())


@app.get("/portfolio")
async def get_portfolio() -> AccountSummary:
    try:
        response = httpx.get(f"{settings.execution_service_url}/account", timeout=15.0)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"execution service unreachable: {e}")

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", response.text),
        )

    return AccountSummary.model_validate(response.json())
