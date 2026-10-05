"""Decision support for TimePressure: evidence-based strategy ranking and lessons."""
from __future__ import annotations

import math
from collections import defaultdict


def build_intelligence_report(strategies, stats, recent_events=(), limit=8):
    """Rank strategies using observed outcomes without treating estimates as facts."""
    rows = []
    recent = list(recent_events)[-200:]
    for strategy in strategies:
        key = strategy.get("id", "unknown")
        history = stats.get(key, {})
        attempts = max(0, int(history.get("attempts", 0)))
        successes = max(0, int(history.get("successes", 0)))
        failures = max(0, int(history.get("failures", 0)))
        revenue = max(0.0, float(history.get("revenueUsd", 0.0)))
        # Beta prior prevents one lucky or failed attempt from dominating.
        observed_success_rate = (successes + 1.0) / (attempts + 2.0)
        revenue_per_attempt = revenue / max(1, attempts)
        base_score = max(0.01, float(strategy.get("score", 0.01)))
        confidence = min(1.0, math.log1p(attempts) / math.log(11))
        learned_multiplier = 0.65 + 0.7 * observed_success_rate
        revenue_multiplier = 1.0 + min(1.0, revenue_per_attempt) * 0.5
        score = base_score * learned_multiplier * revenue_multiplier
        rows.append({
            "id": key,
            "name": strategy.get("name", key),
            "category": strategy.get("category", "unknown"),
            "score": round(score, 4),
            "baseScore": round(base_score, 4),
            "observedSuccessRate": round(observed_success_rate, 3),
            "attempts": attempts,
            "successes": successes,
            "failures": failures,
            "verifiedRevenueUsd": round(revenue, 2),
            "confidence": round(confidence, 3),
            "reason": _reason(attempts, observed_success_rate, revenue),
        })
    rows.sort(key=lambda x: (x["score"], x["verifiedRevenueUsd"], x["confidence"]), reverse=True)
    categories = defaultdict(int)
    diversified = []
    for row in rows:
        if categories[row["category"]] >= 3:
            continue
        diversified.append(row)
        categories[row["category"]] += 1
        if len(diversified) >= max(1, min(20, int(limit))):
            break
    event_counts = defaultdict(int)
    for event in recent:
        event_counts[str(getattr(event, "type", "event"))] += 1
    return {
        "rankedStrategies": diversified,
        "historyCoverage": sum(max(0, int(v.get("attempts", 0))) for v in stats.values()),
        "verifiedRevenueUsd": round(sum(max(0.0, float(v.get("revenueUsd", 0))) for v in stats.values()), 2),
        "recentEventCounts": dict(event_counts),
        "policy": "Observed outcomes influence ranking; unverified reward estimates never count as revenue.",
    }


def _reason(attempts, success_rate, revenue):
    if revenue > 0:
        return "Has recorded revenue; prioritize cautiously and verify new payments."
    if attempts == 0:
        return "No local outcome history; score is primarily heuristic."
    if success_rate >= 0.6:
        return "Past task outcomes are relatively positive, but no revenue is recorded."
    return "Weak or limited past outcomes; test only if cost and risk remain low."
