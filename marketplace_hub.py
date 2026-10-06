#!/usr/bin/env python3
"""Marketplace Hub for TimePressure.

A dependency-free orchestration layer for legitimate agent marketplaces.
Discovery is read-only by default. Mutating actions require explicit operator
enablement and an official marketplace bridge/adapter.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class MarketTask:
    marketplace: str
    task_id: str
    title: str
    description: str
    url: str
    reward_usd: float
    category: str
    status: str
    estimated_minutes: int = 30
    probability: float = 0.0
    risk: float = 0.25
    requires_credentials: bool = True
    execution: str = "manual"


class MarketplaceAdapter:
    name = "base"

    def __init__(self):
        self.enabled = True

    def discover(self, limit: int = 20) -> list[MarketTask]:
        raise NotImplementedError

    def execute(self, task: MarketTask, instruction: str) -> dict[str, Any]:
        return {
            "ok": False,
            "marketplace": self.name,
            "taskId": task.task_id,
            "error": "This adapter is read-only until an official execution path is configured.",
        }


def _http_json(url: str, headers: dict[str, str] | None = None, timeout: int = 12):
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "TimePressure/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _first(data, *keys, default=None):
    if isinstance(data, dict):
        for key in keys:
            if key in data:
                return data[key]
    return default


class ZeroXWorkAdapter(MarketplaceAdapter):
    name = "0xWork"

    def __init__(self):
        super().__init__()
        self.api_url = os.getenv("TIMEPRESSURE_0XWORK_API_URL", "https://api.0xwork.org").rstrip("/")

    def discover(self, limit=20):
        limit = max(1, min(int(limit), 50))
        query = urllib.parse.urlencode({"status": "open", "limit": limit})
        data = _http_json(
            f"{self.api_url}/tasks?{query}",
            {"Accept": "application/json", "User-Agent": "TimePressure/1.0"},
        )
        rows = data.get("tasks", data if isinstance(data, list) else [])
        result = []
        for row in rows[:limit]:
            reward = _first(row, "bounty", "reward", "amount", default=0) or 0
            try:
                reward = float(reward)
            except (TypeError, ValueError):
                reward = 0.0
            task_id = str(_first(row, "chainTaskId", "taskId", "id", default=""))
            if not task_id:
                continue
            title = str(_first(row, "title", "name", default=f"0xWork task {task_id}"))
            result.append(MarketTask(
                self.name, task_id, title,
                str(_first(row, "description", "summary", default="")),
                str(_first(row, "url", "htmlUrl", default=f"https://www.0xwork.org/tasks/{task_id}")),
                reward, str(_first(row, "category", default="general")),
                str(_first(row, "status", default="open")),
                int(_first(row, "estimatedMinutes", default=30) or 30),
                0.35 if reward > 0 else 0.15, 0.35,
                True, "official API/CLI required for write actions",
            ))
        return result


class AgentHansaAdapter(MarketplaceAdapter):
    name = "AgentHansa"

    def __init__(self):
        super().__init__()
        self.base_url = os.getenv("TIMEPRESSURE_AGENTHANSA_BASE_URL", "https://www.agenthansa.com").rstrip("/")
        self.api_key = os.getenv("AGENTHANSA_API_KEY")

    def discover(self, limit=20):
        if not self.api_key:
            return []
        limit = max(1, min(int(limit), 50))
        url = f"{self.base_url}/api/agents/work?" + urllib.parse.urlencode({"page": 1, "per_page": limit, "type": "all"})
        data = _http_json(url, {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "TimePressure/1.0",
        })
        rows = data.get("work", data.get("items", data if isinstance(data, list) else []))
        result = []
        for row in rows[:limit]:
            reward = _first(row, "reward", "bounty", "amount", "price", default=0) or 0
            try:
                reward = float(reward)
            except (TypeError, ValueError):
                reward = 0.0
            task_id = str(_first(row, "id", "task_id", "quest_id", "assignment_id", default=""))
            if not task_id:
                continue
            result.append(MarketTask(
                self.name, task_id,
                str(_first(row, "title", "name", default=f"AgentHansa task {task_id}")),
                str(_first(row, "description", "brief", "summary", default="")),
                str(_first(row, "url", "html_url", default="https://www.agenthansa.com/explore")),
                reward, str(_first(row, "category", "type", default="general")),
                str(_first(row, "status", default="open")),
                int(_first(row, "estimated_minutes", "estimatedMinutes", default=30) or 30),
                0.30 if reward > 0 else 0.12, 0.30,
                True, "authenticated AgentHansa API",
            ))
        return result


class OfficialBridgeAdapter(MarketplaceAdapter):
    """Adapter for marketplaces whose official CLI/SDK is the source of truth.

    The bridge command receives JSON on stdin and must return JSON on stdout.
    This keeps TimePressure Python-only while allowing official Node/CLI SDKs
    to be used when the operator has explicitly installed them.
    """

    def __init__(self, name: str, env_name: str):
        self.name = name
        self.env_name = env_name
        self.command = os.getenv(env_name, "").strip()

    def discover(self, limit=20):
        if not self.command:
            return []
        payload = json.dumps({"action": "discover", "limit": int(limit)})
        proc = subprocess.run(
            shlex.split(self.command), input=payload, text=True,
            capture_output=True, timeout=30, check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"{self.name} bridge failed")
        data = json.loads(proc.stdout or "{}")
        rows = data.get("tasks", data.get("orders", []))
        result = []
        for row in rows[:limit]:
            result.append(MarketTask(
                self.name,
                str(_first(row, "id", "task_id", "order_id", default="")),
                str(_first(row, "title", "name", default="")),
                str(_first(row, "description", "criteria", "brief", default="")),
                str(_first(row, "url", default="")),
                float(_first(row, "reward_usd", "reward", "bounty", "price", default=0) or 0),
                str(_first(row, "category", "type", default="general")),
                str(_first(row, "status", default="open")),
                int(_first(row, "estimated_minutes", default=30) or 30),
                float(_first(row, "probability", default=0.25) or 0.25),
                float(_first(row, "risk", default=0.30) or 0.30),
                True, "official CLI/SDK bridge",
            ))
        return [x for x in result if x.task_id]

    def execute(self, task, instruction):
        if not self.command:
            return {"ok": False, "error": f"{self.name} bridge is not configured."}
        payload = json.dumps({
            "action": "execute",
            "task": asdict(task),
            "instruction": instruction,
        })
        proc = subprocess.run(
            shlex.split(self.command), input=payload, text=True,
            capture_output=True, timeout=300, check=False,
        )
        if proc.returncode != 0:
            return {"ok": False, "error": proc.stderr.strip() or f"{self.name} bridge failed"}
        try:
            return json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            return {"ok": True, "output": proc.stdout.strip()}


def adapters():
    return [
        ZeroXWorkAdapter(),
        AgentHansaAdapter(),
        OfficialBridgeAdapter("Clustly", "TIMEPRESSURE_CLUSTLY_BRIDGE"),
        OfficialBridgeAdapter("Daydreams/Lucid", "TIMEPRESSURE_DAYDREAMS_BRIDGE"),
    ]


def score(task: MarketTask) -> float:
    minutes = max(1, task.estimated_minutes)
    expected = task.reward_usd * max(0.0, min(1.0, task.probability))
    risk_adjusted = expected * (1.0 - 0.65 * max(0.0, min(1.0, task.risk)))
    return round(risk_adjusted / (minutes / 60.0), 4)


def discover_all(limit_per_marketplace=10):
    found = []
    errors = []
    for adapter in adapters():
        try:
            found.extend(adapter.discover(limit_per_marketplace))
        except Exception as exc:
            errors.append({"marketplace": adapter.name, "error": str(exc)})
    found.sort(key=score, reverse=True)
    return found, errors


def snapshot():
    rows = []
    for adapter in adapters():
        configured = bool(getattr(adapter, "api_key", None) or getattr(adapter, "command", None))
        rows.append({
            "marketplace": adapter.name,
            "configured": configured,
            "mode": "live" if configured else "not_configured",
        })
    return rows


def run_once(limit_per_marketplace=10):
    tasks, errors = discover_all(limit_per_marketplace)
    return {
        "timestamp": time.time(),
        "marketplaces": snapshot(),
        "tasks": [dict(asdict(task), score=score(task)) for task in tasks],
        "errors": errors,
        "next": dict(asdict(tasks[0]), score=score(tasks[0])) if tasks else None,
    }


def execute_task(marketplace, task_id, instruction):
    if os.getenv("TIMEPRESSURE_MARKETPLACE_AUTOMATION", "false").lower() != "true":
        return {"ok": False, "error": "Marketplace write automation is disabled. Set TIMEPRESSURE_MARKETPLACE_AUTOMATION=true only after reviewing credentials and platform terms."}
    if os.getenv("TIMEPRESSURE_MARKETPLACE_ELIGIBLE", "false").lower() != "true":
        return {"ok": False, "error": "Operator eligibility gate is not enabled."}
    for adapter in adapters():
        if adapter.name.lower() == marketplace.lower():
            task = next((x for x in adapter.discover(50) if x.task_id == str(task_id)), None)
            if not task:
                return {"ok": False, "error": "Task not found in current marketplace feed."}
            return adapter.execute(task, instruction)
    return {"ok": False, "error": f"Unknown marketplace: {marketplace}"}
