#!/usr/bin/env python3
"""OKX.AI Task Marketplace adapter for TimePressure.

This module intentionally targets OKX.AI (the AI task/agent marketplace), not
the OKX exchange/trading APIs.

Write operations are available only through an operator-configured official
Onchain OS/OKX.AI bridge. No undocumented OKX endpoint is guessed here.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urljoin, urlparse


OKX_AI_URL = os.getenv("TIMEPRESSURE_OKX_AI_URL", "https://okx.ai").rstrip("/")
OKX_AI_TASK_HALL_URL = os.getenv("TIMEPRESSURE_OKX_AI_TASK_HALL_URL", OKX_AI_URL)
OKX_AI_BRIDGE = os.getenv("TIMEPRESSURE_OKX_AI_BRIDGE", "").strip()
OKX_AI_TASK_SELECTOR = os.getenv(
    "TIMEPRESSURE_OKX_AI_TASK_SELECTOR",
    "a[href*='task'],a[href*='Task'],a[href*='tasks']",
)


@dataclass
class OKXAITask:
    marketplace: str
    task_id: str
    title: str
    description: str
    url: str
    reward_usd: float
    category: str
    status: str
    estimated_minutes: int = 30
    probability: float = 0.25
    risk: float = 0.30
    requires_credentials: bool = True
    execution: str = "official_okx_ai_bridge"


def _first(obj: dict[str, Any], *keys: str, default=None):
    for key in keys:
        if key in obj:
            return obj[key]
    return default


def _money(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else 0.0


def _minutes(value: Any) -> int:
    try:
        return max(1, int(float(value)))
    except (TypeError, ValueError):
        return 30


def _bridge(action: str, **payload) -> dict[str, Any]:
    if not OKX_AI_BRIDGE:
        raise RuntimeError(
            "TIMEPRESSURE_OKX_AI_BRIDGE is not configured. "
            "Configure the official OKX.AI/Onchain OS bridge before enabling write actions."
        )
    request = {"action": action, **payload}
    proc = subprocess.run(
        shlex.split(OKX_AI_BRIDGE),
        input=json.dumps(request),
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "OKX.AI bridge failed")
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("OKX.AI bridge returned invalid JSON") from exc


def _normalize(rows: list[dict[str, Any]], limit: int) -> list[OKXAITask]:
    result: list[OKXAITask] = []
    for row in rows[:limit]:
        task_id = str(_first(row, "id", "task_id", "taskId", "order_id", default="")).strip()
        if not task_id:
            continue
        result.append(
            OKXAITask(
                marketplace="OKX.AI",
                task_id=task_id,
                title=str(_first(row, "title", "name", "task_title", default=f"OKX.AI task {task_id}")),
                description=str(_first(row, "description", "brief", "requirements", "summary", default="")),
                url=str(_first(row, "url", "task_url", "html_url", default=OKX_AI_TASK_HALL_URL)),
                reward_usd=_money(_first(row, "reward_usd", "reward", "bounty", "budget", "price", default=0)),
                category=str(_first(row, "category", "type", default="general")),
                status=str(_first(row, "status", default="open")),
                estimated_minutes=_minutes(_first(row, "estimated_minutes", "estimatedMinutes", "deadline_minutes", default=30)),
                probability=max(0.0, min(1.0, float(_first(row, "probability", default=0.25) or 0.25))),
                risk=max(0.0, min(1.0, float(_first(row, "risk", default=0.30) or 0.30))),
                requires_credentials=True,
            )
        )
    return result


def discover_via_bridge(limit: int) -> list[OKXAITask]:
    data = _bridge("discover", limit=limit)
    rows = data.get("tasks", data.get("orders", []))
    if not isinstance(rows, list):
        raise RuntimeError("OKX.AI bridge discovery response has no task list")
    return _normalize(rows, limit)


def discover_via_browser(limit: int) -> list[OKXAITask]:
    """Best-effort read-only fallback for the public OKX.AI task hall.

    It does not log in, solve challenges, or submit anything. Because the
    marketplace UI can change, the task selector is configurable.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is required for the OKX.AI browser fallback") from exc

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(OKX_AI_TASK_HALL_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1000)
            locator = page.locator(OKX_AI_TASK_SELECTOR)
            tasks: list[OKXAITask] = []
            seen: set[str] = set()
            count = min(max(1, limit), 50)
            for i in range(min(locator.count(), count * 3)):
                item = locator.nth(i)
                href = item.get_attribute("href") or ""
                title = (item.inner_text(timeout=3000) or "").strip()
                if not href or not title:
                    continue
                url = urljoin(page.url, href)
                parsed = urlparse(url)
                if parsed.netloc not in {"okx.ai", "www.okx.ai"}:
                    continue
                task_id = parsed.path.rstrip("/").split("/")[-1] or href
                if task_id in seen:
                    continue
                seen.add(task_id)
                tasks.append(
                    OKXAITask(
                        marketplace="OKX.AI",
                        task_id=task_id,
                        title=title[:300],
                        description="Discovered from the public OKX.AI task marketplace page.",
                        url=url,
                        reward_usd=0.0,
                        category="unknown",
                        status="open",
                        estimated_minutes=30,
                        probability=0.15,
                        risk=0.35,
                        execution="manual_or_official_okx_ai_bridge",
                    )
                )
                if len(tasks) >= count:
                    break
            return tasks
        finally:
            browser.close()


def discover(limit: int = 20) -> list[OKXAITask]:
    limit = max(1, min(int(limit), 50))
    if OKX_AI_BRIDGE:
        return discover_via_bridge(limit)
    return discover_via_browser(limit)


def score(task: OKXAITask) -> float:
    minutes = max(1, task.estimated_minutes)
    expected = task.reward_usd * max(0.0, min(1.0, task.probability))
    risk_adjusted = expected * (1.0 - 0.65 * max(0.0, min(1.0, task.risk)))
    return round(risk_adjusted / (minutes / 60.0), 4)


def snapshot() -> list[dict[str, Any]]:
    return [{
        "marketplace": "OKX.AI",
        "configured": bool(OKX_AI_BRIDGE),
        "mode": "official_bridge" if OKX_AI_BRIDGE else "read_only_browser",
        "taskHall": OKX_AI_TASK_HALL_URL,
        "writeEnabled": os.getenv("TIMEPRESSURE_MARKETPLACE_AUTOMATION", "false").lower() == "true",
    }]


def execute_task(task: OKXAITask, instruction: str) -> dict[str, Any]:
    if os.getenv("TIMEPRESSURE_MARKETPLACE_AUTOMATION", "false").lower() != "true":
        return {"ok": False, "marketplace": "OKX.AI", "error": "Write automation is disabled."}
    if os.getenv("TIMEPRESSURE_MARKETPLACE_ELIGIBLE", "false").lower() != "true":
        return {"ok": False, "marketplace": "OKX.AI", "error": "Operator eligibility gate is disabled."}
    if not OKX_AI_BRIDGE:
        return {
            "ok": False,
            "marketplace": "OKX.AI",
            "error": "No official OKX.AI/Onchain OS bridge configured; browser fallback is read-only.",
        }
    return _bridge("execute", task=asdict(task), instruction=instruction)


def run_once(limit: int = 10) -> dict[str, Any]:
    tasks = discover(limit)
    ranked = [dict(asdict(x), score=score(x)) for x in tasks]
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {
        "timestamp": time.time(),
        "marketplaces": snapshot(),
        "tasks": ranked,
        "next": ranked[0] if ranked else None,
    }
