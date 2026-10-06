"""Compatibility facade for the OKX.AI-only TimePressure marketplace layer.

The old multi-marketplace hub was intentionally removed. Keep this module so
older imports do not break while exposing only OKX.AI.
"""
from __future__ import annotations

from dataclasses import asdict
from okx_ai import OKXAITask, discover, execute_task, run_once, score, snapshot


MarketTask = OKXAITask


def discover_all(limit_per_marketplace: int = 10):
    try:
        return discover(limit_per_marketplace), []
    except Exception as exc:
        return [], [{"marketplace": "OKX.AI", "error": str(exc)}]


def execute_task_by_marketplace(marketplace: str, task_id: str, instruction: str):
    if marketplace.lower() != "okx.ai":
        return {"ok": False, "error": "TimePressure is OKX.AI-only."}
    task = next((x for x in discover(50) if x.task_id == str(task_id)), None)
    if not task:
        return {"ok": False, "error": "Task not found."}
    return execute_task(task, instruction)


def execute_task(marketplace: str, task_id: str, instruction: str):
    return execute_task_by_marketplace(marketplace, task_id, instruction)


__all__ = [
    "MarketTask",
    "discover_all",
    "execute_task",
    "run_once",
    "score",
    "snapshot",
]
