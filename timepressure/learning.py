"""Online learning for TimePressure.

Learns from observed outcomes without inventing revenue. Scores strategy families using
success/failure observations and verified payments when available.
"""
from __future__ import annotations

import math
import time
from typing import Any


def _bucket(learning: dict[str, Any], key: str) -> dict[str, Any]:
    strategies = learning.setdefault("strategies", {})
    item = strategies.setdefault(key, {
        "attempts": 0,
        "successes": 0,
        "failures": 0,
        "verifiedRevenueCents": 0,
        "verifiedPayments": 0,
        "lastOutcomeAt": 0,
    })
    return item


def observe(learning: dict[str, Any], key: str, success: bool,
            verified_revenue_cents: int = 0) -> None:
    item = _bucket(learning, key or "unknown")
    item["attempts"] += 1
    if success:
        item["successes"] += 1
    else:
        item["failures"] += 1
    if verified_revenue_cents > 0:
        item["verifiedRevenueCents"] += int(verified_revenue_cents)
        item["verifiedPayments"] += 1
    item["lastOutcomeAt"] = time.time()


def strategy_multiplier(learning: dict[str, Any], key: str) -> float:
    item = _bucket(learning, key or "unknown")
    attempts = int(item["attempts"])
    successes = int(item["successes"])
    # Beta posterior mean with a neutral prior. Shrinks noisy early observations.
    posterior = (successes + 1.0) / (attempts + 2.0)
    confidence = min(1.0, attempts / 8.0)
    return 0.85 + confidence * (0.55 * posterior + 0.15)


def rerank(candidates: list[dict], learning: dict[str, Any]) -> list[dict]:
    for item in candidates:
        key = str(item.get("id") or item.get("category") or "unknown")
        item["learningMultiplier"] = round(strategy_multiplier(learning, key), 4)
        item["score"] = float(item.get("score", 0)) * item["learningMultiplier"]
    return sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)


def summary(learning: dict[str, Any]) -> dict[str, Any]:
    strategies = learning.get("strategies", {})
    total = sum(int(x.get("attempts", 0)) for x in strategies.values())
    successful = sum(int(x.get("successes", 0)) for x in strategies.values())
    verified = sum(int(x.get("verifiedRevenueCents", 0)) for x in strategies.values())
    return {
        "strategiesLearned": len(strategies),
        "observations": total,
        "successfulActions": successful,
        "verifiedRevenueCents": verified,
        "globalSuccessRate": round(successful / total, 4) if total else None,
    }
