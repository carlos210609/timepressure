"""Autonomy policy engine for TimePressure.

Keeps autonomy configurable and bounded. It never grants permissions to a
marketplace; connector/security policy remains authoritative.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

LEVELS = {
    0: "manual",
    1: "suggest",
    2: "plan",
    3: "execute_permitted",
    4: "recover_and_replan",
    5: "maximum_within_limits",
}

DEFAULT_LIMITS = {
    "max_task_value_usd": 100.0,
    "min_expected_value_usd": 0.50,
    "max_daily_actions": 100,
    "max_daily_cost_usd": 10.0,
    "min_success_probability": 0.65,
    "max_risk": 0.35,
    "max_retries": 2,
}


class AutonomyPolicy:
    def __init__(self, data_dir: str):
        self.path = Path(data_dir) / "autonomy.json"
        self.data = self._load()

    def _load(self):
        default = {
            "level": 3,
            "limits": dict(DEFAULT_LIMITS),
            "day": time.strftime("%Y-%m-%d"),
            "actions_today": 0,
            "cost_today_usd": 0.0,
            "updated_at": time.time(),
        }
        try:
            data = json.loads(self.path.read_text())
            default.update(data)
            default["limits"] = {**DEFAULT_LIMITS, **data.get("limits", {})}
        except (OSError, ValueError, TypeError):
            data = default
        if default["day"] != time.strftime("%Y-%m-%d"):
            default["day"] = time.strftime("%Y-%m-%d")
            default["actions_today"] = 0
            default["cost_today_usd"] = 0.0
        return default

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    @property
    def level(self):
        return int(self.data["level"])

    def set_level(self, level: int):
        level = int(level)
        if level not in LEVELS:
            raise ValueError("Autonomy level must be between 0 and 5.")
        self.data["level"] = level
        self.data["updated_at"] = time.time()
        self.save()
        return self.snapshot()

    def set_limit(self, key: str, value: float):
        if key not in DEFAULT_LIMITS:
            raise ValueError("Unknown autonomy limit: " + key)
        value = float(value)
        if value < 0:
            raise ValueError("Limit cannot be negative.")
        if key == "min_success_probability" and value > 1:
            raise ValueError("Probability must be between 0 and 1.")
        if key == "max_risk" and value > 1:
            raise ValueError("Risk must be between 0 and 1.")
        self.data["limits"][key] = value
        self.data["updated_at"] = time.time()
        self.save()
        return self.snapshot()

    def can_act(self, *, expected_value_usd=0.0, task_value_usd=0.0,
                probability=1.0, risk=0.0, cost_usd=0.0):
        if self.level < 3:
            return False, "Autonomy level requires operator approval."
        limits = self.data["limits"]
        if task_value_usd > limits["max_task_value_usd"]:
            return False, "Task value exceeds autonomy limit."
        if expected_value_usd < limits["min_expected_value_usd"]:
            return False, "Expected value is below autonomy threshold."
        if probability < limits["min_success_probability"]:
            return False, "Success probability is below autonomy threshold."
        if risk > limits["max_risk"]:
            return False, "Risk exceeds autonomy threshold."
        self._roll_day()
        if self.data["actions_today"] >= limits["max_daily_actions"]:
            return False, "Daily action limit reached."
        if self.data["cost_today_usd"] + cost_usd > limits["max_daily_cost_usd"]:
            return False, "Daily cost limit reached."
        return True, "allowed"

    def record_action(self, cost_usd=0.0):
        self._roll_day()
        self.data["actions_today"] += 1
        self.data["cost_today_usd"] += max(0.0, float(cost_usd))
        self.save()

    def _roll_day(self):
        today = time.strftime("%Y-%m-%d")
        if self.data.get("day") != today:
            self.data["day"] = today
            self.data["actions_today"] = 0
            self.data["cost_today_usd"] = 0.0

    def snapshot(self):
        self._roll_day()
        return {
            "level": self.level,
            "mode": LEVELS[self.level],
            "limits": dict(self.data["limits"]),
            "actionsToday": self.data["actions_today"],
            "costTodayUsd": round(self.data["cost_today_usd"], 4),
            "updatedAt": self.data["updated_at"],
        }


def get_policy(data_dir: str) -> AutonomyPolicy:
    return AutonomyPolicy(data_dir)
