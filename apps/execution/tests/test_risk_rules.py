from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.risk_rules import RiskRuleViolation, validate_order

NOW = datetime.now(timezone.utc)


def _order(**overrides):
    defaults = dict(
        action="buy",
        position_size_pct=2.0,
        quantity=1,
        price=100.0,
        proposal_created_at=NOW,
    )
    defaults.update(overrides)
    return defaults


def test_valid_order_does_not_raise():
    validate_order(**_order())


@pytest.mark.parametrize("action", ["hold", "short", "buy_to_cover", ""])
def test_non_buy_sell_actions_are_rejected(action):
    with pytest.raises(RiskRuleViolation, match="not executable"):
        validate_order(**_order(action=action))


def test_sell_is_a_valid_action():
    validate_order(**_order(action="sell"))


@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_non_positive_quantity_is_rejected(quantity):
    with pytest.raises(RiskRuleViolation, match="quantity must be positive"):
        validate_order(**_order(quantity=quantity))


def test_position_size_at_the_cap_is_accepted():
    validate_order(**_order(position_size_pct=settings.max_position_pct_hard_cap))


def test_position_size_over_the_cap_is_rejected():
    with pytest.raises(RiskRuleViolation, match="exceeds the hard cap"):
        validate_order(
            **_order(position_size_pct=settings.max_position_pct_hard_cap + 0.01)
        )


def test_notional_at_the_cap_is_accepted():
    quantity = 10
    price = settings.max_notional_usd_hard_cap / quantity
    validate_order(**_order(quantity=quantity, price=price))


def test_notional_over_the_cap_is_rejected():
    quantity = 10
    price = settings.max_notional_usd_hard_cap / quantity + 1.0
    with pytest.raises(RiskRuleViolation, match="exceeds the hard cap"):
        validate_order(**_order(quantity=quantity, price=price))


def test_proposal_within_age_limit_is_accepted():
    created_at = NOW - timedelta(hours=settings.max_proposal_age_hours - 1)
    validate_order(**_order(proposal_created_at=created_at))


def test_stale_proposal_is_rejected():
    created_at = NOW - timedelta(hours=settings.max_proposal_age_hours + 1)
    with pytest.raises(RiskRuleViolation, match="staleness limit"):
        validate_order(**_order(proposal_created_at=created_at))
