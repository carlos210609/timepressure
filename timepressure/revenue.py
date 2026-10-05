"""Revenue Engine: expected-value opportunity selection and verified P&L tracking.

Forecasts are estimates. Only explicit, externally verified revenue belongs in the
verified ledger. The engine never fabricates payments.
"""
from __future__ import annotations
import time, uuid
from dataclasses import asdict, dataclass


@dataclass
class RevenueOpportunity:
    id: str
    source: str
    title: str
    category: str
    url: str
    estimated_revenue_cents: int
    estimated_cost_cents: int
    estimated_minutes: int
    probability: float
    risk: float
    evidence: str
    status: str = "candidate"
    created_at: float = 0.0


@dataclass
class RevenueAttempt:
    id: str
    opportunity_id: str
    status: str
    started_at: float
    finished_at: float | None = None
    cost_cents: int = 0
    verified_revenue_cents: int = 0
    reference: str | None = None


def new_opportunity(source, title, category="service", url="", revenue_cents=0,
                    cost_cents=0, minutes=60, probability=0.0, risk=0.0,
                    evidence=""):
    return RevenueOpportunity(
        str(uuid.uuid4()), str(source), str(title), str(category), str(url),
        max(0, int(revenue_cents)), max(0, int(cost_cents)), max(1, int(minutes)),
        max(0.0, min(1.0, float(probability))),
        max(0.0, min(1.0, float(risk))), str(evidence),
        "candidate", time.time(),
    )


def score_revenue_opportunity(item) -> dict:
    """Rank by expected profit/hour while penalizing risk and weak evidence."""
    revenue = max(0, int(item.estimated_revenue_cents))
    cost = max(0, int(item.estimated_cost_cents))
    probability = max(0.0, min(1.0, float(item.probability)))
    risk = max(0.0, min(1.0, float(item.risk)))
    minutes = max(1, int(item.estimated_minutes))
    evidence = 0.0 if not item.evidence else 1.0
    expected_profit = probability * revenue - cost
    risk_adjusted = expected_profit * (1.0 - 0.65 * risk) * (0.65 + 0.35 * evidence)
    hourly = risk_adjusted / (minutes / 60.0)
    return {
        "id": item.id,
        "expectedProfitCents": round(expected_profit, 2),
        "riskAdjustedProfitCents": round(risk_adjusted, 2),
        "hourlyValueCents": round(hourly, 2),
        "probability": round(probability, 4),
        "risk": round(risk, 4),
        "evidence": bool(item.evidence),
        "score": round(hourly, 2),
    }


def rank_opportunities(items, minimum_probability=0.15, max_minutes=60):
    scored = []
    for item in items:
        if item.status not in ("candidate", "queued"):
            continue
        if item.probability < minimum_probability:
            continue
        if max_minutes is not None and int(item.estimated_minutes) > int(max_minutes):
            continue
        scored.append((score_revenue_opportunity(item)["score"], item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


def select_next_opportunity(items):
    ranked = rank_opportunities(items, max_minutes=60)
    if not ranked:
        return None
    item = ranked[0]
    item.status = "queued"
    return item


def start_attempt(item) -> RevenueAttempt:
    item.status = "active"
    return RevenueAttempt(str(uuid.uuid4()), item.id, "active", time.time())


def complete_attempt(attempt, verified_revenue_cents=0, cost_cents=0, reference=None):
    attempt.finished_at = time.time()
    attempt.verified_revenue_cents = max(0, int(verified_revenue_cents))
    attempt.cost_cents = max(0, int(cost_cents))
    attempt.reference = reference
    attempt.status = "paid" if attempt.verified_revenue_cents > 0 else "completed"
    return attempt


def cancel_attempt(attempt, reason="cancelled"):
    attempt.finished_at = time.time()
    attempt.status = str(reason)
    return attempt


def revenue_snapshot(opportunities, attempts, verified_revenue_cents=0):
    gross = max(0, int(verified_revenue_cents))
    costs = sum(max(0, int(x.cost_cents)) for x in attempts)
    paid = sum(1 for x in attempts if x.status == "paid")
    active = sum(1 for x in attempts if x.status == "active")
    return {
        "opportunities": len(opportunities),
        "activeAttempts": active,
        "paidAttempts": paid,
        "verifiedRevenueCents": gross,
        "verifiedCostCents": costs,
        "netProfitCents": gross - costs,
        "roiPct": round((gross - costs) / costs * 100, 2) if costs else None,
    }


def opportunity_to_dict(item):
    return asdict(item)


def attempt_to_dict(item):
    return asdict(item)


def seed_from_strategy(strategy, *, source="strategy_catalog"):
    """Convert a strategy estimate into an opportunity; estimates are deliberately conservative."""
    value = {"high": 15000, "medium": 5000}.get(strategy.get("value"), 2500)
    minutes = {"short": 45, "medium": 180, "long": 480}.get(strategy.get("time"), 180)
    probability = {"high": 0.18, "medium": 0.12}.get(strategy.get("value"), 0.08)
    risk = 0.15 if strategy.get("automation") == "high" else 0.25
    return new_opportunity(
        source, strategy.get("name", strategy.get("id", "strategy")),
        strategy.get("category", "service"), revenue_cents=value,
        minutes=minutes, probability=probability, risk=risk,
        evidence="catalog estimate; payment still unverified",
    )
