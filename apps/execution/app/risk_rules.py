"""Hard, deterministic risk checks re-validated independently of the research
system's own Risk module - this service does not trust its caller. No LLM
involved anywhere here."""

from datetime import datetime, timedelta, timezone

from app.config import settings


class RiskRuleViolation(Exception):
    pass


def validate_order(
    action: str,
    position_size_pct: float,
    quantity: int,
    price: float,
    proposal_created_at: datetime,
) -> None:
    if action not in ("buy", "sell"):
        raise RiskRuleViolation(f"action {action!r} is not executable (only buy/sell)")

    if quantity <= 0:
        raise RiskRuleViolation("quantity must be positive")

    if position_size_pct > settings.max_position_pct_hard_cap:
        raise RiskRuleViolation(
            f"proposed position size {position_size_pct:.2f}% exceeds the hard cap "
            f"{settings.max_position_pct_hard_cap:.2f}%"
        )

    notional = quantity * price
    if notional > settings.max_notional_usd_hard_cap:
        raise RiskRuleViolation(
            f"order notional ${notional:,.2f} exceeds the hard cap "
            f"${settings.max_notional_usd_hard_cap:,.2f}"
        )

    age = datetime.now(timezone.utc) - proposal_created_at
    if age > timedelta(hours=settings.max_proposal_age_hours):
        raise RiskRuleViolation(
            f"trade proposal is {age.total_seconds() / 3600:.1f}h old, exceeding "
            f"the {settings.max_proposal_age_hours}h staleness limit - re-run "
            f"research before executing"
        )
