from timepressure.revenue import (
    complete_attempt, new_opportunity, rank_opportunities, revenue_snapshot,
    score_revenue_opportunity, start_attempt,
)


def test_expected_value_prefers_fast_profitable_opportunity():
    fast = new_opportunity("test", "Fast", revenue_cents=10000, minutes=30, probability=.5, risk=.1, evidence="payment page")
    slow = new_opportunity("test", "Slow", revenue_cents=30000, minutes=600, probability=.5, risk=.1, evidence="payment page")
    assert score_revenue_opportunity(fast)["score"] > score_revenue_opportunity(slow)["score"]
    assert rank_opportunities([fast, slow])[0].title == "Fast"


def test_attempt_does_not_equal_verified_ledger():
    item = new_opportunity("test", "Service", revenue_cents=5000, minutes=60, probability=.5, evidence="quote")
    attempt = start_attempt(item)
    complete_attempt(attempt, verified_revenue_cents=5000, cost_cents=100)
    snapshot = revenue_snapshot([item], [attempt], verified_revenue_cents=0)
    assert snapshot["verifiedRevenueCents"] == 0
    assert snapshot["verifiedCostCents"] == 100
    assert snapshot["netProfitCents"] == -100


def test_risk_and_probability_are_bounded():
    item = new_opportunity("x", "x", probability=4, risk=-2)
    score = score_revenue_opportunity(item)
    assert score["probability"] == 1.0
    assert score["risk"] == 0.0
