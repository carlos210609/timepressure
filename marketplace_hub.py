"""Compatibility facade for the selectable TimePressure marketplace layer."""
from __future__ import annotations
from marketplace_registry import (
    active_id, discover_active, execute_active, list_marketplaces,
    score_active, status as marketplace_status,
)

MarketTask = object

def discover_all(limit_per_marketplace: int = 10):
    try:
        return discover_active(limit_per_marketplace), []
    except Exception as exc:
        return [], [{"marketplace": marketplace_status()["active"]["name"], "error": str(exc)}]

def score(task):
    return score_active(task)

def execute_task_by_marketplace(marketplace: str, task_id: str, instruction: str):
    active = marketplace_status()["active"]["id"]
    requested = marketplace.strip().lower().replace("-", "_")
    if requested != active:
        return {"ok": False, "error": f"Only the active marketplace can execute tasks. Active: {active}."}
    return execute_active(task_id, instruction)

def execute_task(marketplace: str, task_id: str, instruction: str):
    return execute_task_by_marketplace(marketplace, task_id, instruction)

def snapshot():
    return list_marketplaces()

__all__ = ["MarketTask","discover_all","execute_task","active_id","discover_active",
           "execute_task_by_marketplace","execute_task","score","score_active","snapshot",
           "marketplace_status"]
