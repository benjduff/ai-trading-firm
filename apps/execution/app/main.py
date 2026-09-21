from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.broker import BrokerError, get_broker
from app.db import get_db
from app.db_models import ExecutedOrderRecord
from app.market_data import MarketDataError
from app.portfolio import get_account_summary, get_positions
from app.readonly_models import HumanDecisionRecord, TradeProposalRecord
from app.risk_rules import RiskRuleViolation, validate_order
from app.schemas import (
    AccountSummaryResponse,
    ExecutedOrder,
    ExecuteRequest,
    PositionResponse,
)

app = FastAPI(title="AI Trading Firm Execution Service", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-trading-firm-execution"}


@app.post("/execute", status_code=201)
def execute_order(
    request: ExecuteRequest, db: Session = Depends(get_db)
) -> ExecutedOrder:
    proposal = db.get(TradeProposalRecord, request.trade_proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="trade proposal not found")

    existing = (
        db.query(ExecutedOrderRecord)
        .filter(ExecutedOrderRecord.trade_proposal_id == proposal.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="an order has already been submitted for this trade proposal",
        )

    # Re-validated independently - this service does not trust its caller's word
    # that a human approved this. No autonomous execution, ever.
    decision = (
        db.query(HumanDecisionRecord)
        .filter(HumanDecisionRecord.trade_proposal_id == proposal.id)
        .order_by(HumanDecisionRecord.decided_at.desc())
        .first()
    )
    if decision is None or decision.action != "approve":
        raise HTTPException(
            status_code=403,
            detail="no approved human decision found for this trade proposal; "
            "this service never executes without one",
        )

    if proposal.action not in ("buy", "sell"):
        raise HTTPException(
            status_code=400,
            detail=f"action {proposal.action!r} is not executable (only buy/sell)",
        )

    if proposal.position_size_pct is None:
        raise HTTPException(
            status_code=400, detail="trade proposal has no position size"
        )

    broker = get_broker()

    try:
        price = broker.get_last_price(proposal.ticker)
        equity = broker.get_account_equity()
    except (MarketDataError, BrokerError) as e:
        raise HTTPException(status_code=502, detail=str(e))

    quantity = int((equity * proposal.position_size_pct / 100.0) // price)

    try:
        validate_order(
            action=proposal.action,
            position_size_pct=proposal.position_size_pct,
            quantity=quantity,
            price=price,
            proposal_created_at=proposal.created_at,
        )
    except RiskRuleViolation as e:
        raise HTTPException(status_code=400, detail=f"risk rule violation: {e}")

    try:
        result = broker.place_market_order(proposal.ticker, proposal.action, quantity)
    except BrokerError as e:
        raise HTTPException(status_code=502, detail=f"broker order failed: {e}")

    stop_loss_price = None
    stop_order_error = None
    if proposal.stop_loss_distance_pct is not None and result.filled_price:
        distance = proposal.stop_loss_distance_pct / 100.0
        if proposal.action == "buy":
            stop_loss_price = result.filled_price * (1 - distance)
            stop_side = "sell"
        else:
            stop_loss_price = result.filled_price * (1 + distance)
            stop_side = "buy"
        try:
            broker.place_stop_order(proposal.ticker, stop_side, quantity, stop_loss_price)
        except BrokerError as e:
            # Entry order already filled; a failed stop-loss doesn't unwind it, but
            # must be surfaced so a human can place one manually.
            stop_order_error = f"stop-loss order failed: {e}"

    record = ExecutedOrderRecord(
        trade_proposal_id=proposal.id,
        human_decision_id=decision.id,
        ticker=proposal.ticker,
        side=proposal.action,
        quantity=quantity,
        order_type="market",
        broker=broker.name,
        broker_order_id=result.broker_order_id,
        stop_loss_price=stop_loss_price,
        status=result.status,
        filled_price=result.filled_price,
        filled_at=datetime.now(timezone.utc) if result.status == "filled" else None,
        error=stop_order_error,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ExecutedOrder.model_validate(record)


@app.get("/orders/{trade_proposal_id}")
async def get_order(
    trade_proposal_id: UUID, db: Session = Depends(get_db)
) -> ExecutedOrder:
    record = (
        db.query(ExecutedOrderRecord)
        .filter(ExecutedOrderRecord.trade_proposal_id == trade_proposal_id)
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=404, detail="no order found for this trade proposal"
        )
    return ExecutedOrder.model_validate(record)


@app.get("/positions")
def list_positions(db: Session = Depends(get_db)) -> list[PositionResponse]:
    orders = db.query(ExecutedOrderRecord).all()
    positions = get_positions(orders, get_broker())
    return [PositionResponse.model_validate(p) for p in positions]


@app.get("/account")
def get_account(db: Session = Depends(get_db)) -> AccountSummaryResponse:
    orders = db.query(ExecutedOrderRecord).all()
    try:
        summary = get_account_summary(orders, get_broker())
    except BrokerError as e:
        raise HTTPException(status_code=502, detail=f"broker error: {e}")
    return AccountSummaryResponse.model_validate(summary)
