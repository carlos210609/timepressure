"""Deterministic guardrails for focused, evidence-driven agent decisions.

The model supplies judgment; this module prevents thrashing, duplicate actions, and
unnecessary parallelism between ticks.
"""
from __future__ import annotations

import hashlib
import time


MAX_ACTIONS_PER_TICK = 1
FOCUS_TTL_TICKS = 3
MAX_CONSECUTIVE_FAILURES = 2


def action_key(action: str, input_text: str) -> str:
    raw = f"{action.strip()}\n{input_text.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def select_action(plan: dict) -> dict | None:
    """Accept exactly one actionable decision; never fan out an unverified plan."""
    if not isinstance(plan, dict):
        raise ValueError("Model response must be a JSON object.")
    actions = plan.get("actions")
    if actions is None and plan.get("action") is not None:
        actions = [{
            "action": plan.get("action"),
            "input": plan.get("input", ""),
            "rationale": plan.get("rationale", ""),
        }]
    if not isinstance(actions, list):
        raise ValueError("Model response must contain an actions array.")
    for item in actions:
        if not isinstance(item, dict):
            continue
        action = item.get("action")
        input_text = item.get("input", "")
        rationale = item.get("rationale", "")
        if not isinstance(action, str) or not isinstance(input_text, str):
            continue
        if action == "none":
            continue
        return {
            "action": action.strip(),
            "input": input_text,
            "rationale": rationale if isinstance(rationale, str) else "",
            "expected_signal": item.get("expected_signal", ""),
            "mode": item.get("mode", "continue"),
        }
    return None


def focus_context(decision: dict, now: float) -> dict:
    """Return only decision state needed by the model."""
    if not decision:
        return {"active": False}
    age = max(0, int(now - float(decision.get("started_at", now))))
    return {
        "active": True,
        "focus": decision.get("focus", ""),
        "mode": decision.get("mode", "continue"),
        "ticks": int(decision.get("ticks", 0)),
        "ageSeconds": age,
        "lastAction": decision.get("last_action", ""),
        "lastInput": decision.get("last_input", ""),
        "lastResult": str(decision.get("last_result", ""))[:3000],
        "consecutiveFailures": int(decision.get("consecutive_failures", 0)),
    }


def start_or_update(decision: dict, action: dict, result: str, success: bool, now: float) -> dict:
    previous = decision or {}
    same_focus = previous.get("action_key") == action_key(action["action"], action["input"])
    failures = int(previous.get("consecutive_failures", 0))
    failures = failures + 1 if not success else 0
    return {
        "focus": action.get("focus") or action.get("rationale", "")[:160],
        "mode": action.get("mode", "continue"),
        "action_key": action_key(action["action"], action["input"]),
        "last_action": action["action"],
        "last_input": action["input"],
        "last_result": str(result)[:4000],
        "last_expected_signal": str(action.get("expected_signal", ""))[:500],
        "last_success": bool(success),
        "consecutive_failures": failures,
        "ticks": int(previous.get("ticks", 0)) + (1 if same_focus else 0),
        "started_at": float(previous.get("started_at", now)) if same_focus else now,
        "updated_at": now,
    }


def should_allow_action(decision: dict, action: dict) -> tuple[bool, str]:
    if not action:
        return False, "no action"
    if decision and decision.get("last_success") and int(decision.get("ticks", 0)) < FOCUS_TTL_TICKS:
        previous_focus = str(decision.get("focus", "")).strip()
        new_focus = str(action.get("focus", "")).strip()
        if previous_focus and new_focus and previous_focus != new_focus and action.get("mode") != "pivot":
            return False, "focus lock active; pivot must be explicit"
    if decision and decision.get("last_action") == action.get("action") and decision.get("last_input") == action.get("input"):
        if decision.get("last_success") and int(decision.get("ticks", 0)) >= FOCUS_TTL_TICKS:
            return False, "exact action repeated after its focus window"
    if decision and int(decision.get("consecutive_failures", 0)) >= MAX_CONSECUTIVE_FAILURES:
        if action_key(action["action"], action["input"]) == decision.get("action_key"):
            return False, "same action failed repeatedly; require a pivot"
    return True, ""
