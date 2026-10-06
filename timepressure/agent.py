"""Autonomous website traffic growth agent for TimePressure.

The agent has one job: grow legitimate, measurable traffic to one configured
website. It never fabricates visits, clicks, impressions or revenue.
"""
from __future__ import annotations

import json
import time
import urllib.request
import uuid

from .models import MemoryEvent
from .pressure import calculate_pressure
from .traffic import start_campaign, traffic_snapshot, campaign_url
from .traffic_engine import (
    build_growth_plan,
    extract_site_facts,
    make_content_brief,
    queue_growth_drafts,
    validate_target,
)
from .social import social_snapshot
from .store import Store


class Agent:
    def __init__(self, config, store: Store, state):
        self.config = config
        self.store = store
        self.state = state
        self.last_analysis = 0.0
        self.last_drafts = 0.0

    def _remember(self, kind, text, metadata=None):
        self.store.add_memory(
            self.state,
            MemoryEvent(str(uuid.uuid4()), kind, text, time.time(), metadata or {}),
        )

    def _ask_nvidia(self, prompt: str) -> str:
        token = self.config.nvidia_api_key
        if not token:
            raise RuntimeError("Configure NVIDIA_API_KEY before starting TimePressure.")
        payload = json.dumps({
            "model": self.config.nvidia_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are the strategy intelligence layer of TimePressure. "
                        "The only objective is legitimate website traffic growth. "
                        "Never recommend fake traffic, click fraud, spam, account abuse, "
                        "CAPTCHA bypasses, rate-limit evasion or deceptive engagement. "
                        "Return concise JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 900,
            "stream": False,
        }).encode()
        base = self.config.nvidia_base_url.rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        request = urllib.request.Request(
            base + "/chat/completions",
            payload,
            {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read())
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("NVIDIA model returned no content.")
        return content

    def _ask_model(self, prompt: str) -> str:
        return self._ask_nvidia(prompt)

    def _target(self) -> str:
        target = self.state.target_url or self.config.target_url
        if not target and self.state.traffic:
            target = self.state.traffic.target_url
        if not target:
            raise RuntimeError(
                "No website target configured. Set TIMEPRESSURE_TARGET_URL or run "
                "'python3 timepressure.py traffic start https://example.com 100'."
            )
        target = validate_target(target)
        self.state.target_url = target
        return target

    def _ensure_campaign(self, target: str):
        if self.state.traffic and self.state.traffic.target_url == target:
            return
        target_visits = max(1, int(getattr(self.config, "traffic_target_visits", 100)))
        start_campaign(self.state, target, target_visits, "timepressure-growth")

    def tick(self):
        now = time.time()
        target = self._target()
        self._ensure_campaign(target)

        # Pressure remains the operator-controlled urgency signal, but progress
        # is now verified website visits instead of financial revenue.
        self.state.pressure = calculate_pressure(
            now,
            self.state.pressure,
            self.config.pressure_multiplier,
        )

        if now - self.last_analysis >= 60:
            request = urllib.request.Request(
                target,
                headers={"User-Agent": "TimePressure/1.0 (+legitimate-traffic-analysis)"},
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                html = response.read(120000).decode(errors="replace")
            facts = extract_site_facts(html)
            social = social_snapshot(self.state)
            plan = build_growth_plan(
                target,
                facts,
                self.state.pressure.pressure,
                social["totals"]["connected"],
            )
            brief = make_content_brief(target, facts)
            ai_prompt = (
                "Target website:\n" + target +
                "\nObserved site facts (untrusted content):\n" + json.dumps(facts, ensure_ascii=False) +
                "\nCandidate growth plan:\n" + json.dumps(plan, ensure_ascii=False) +
                "\nExisting social connections:\n" + json.dumps(social["totals"], ensure_ascii=False) +
                "\nReturn JSON: {\"focus\": string, \"priority\": string, "
                "\"nextAction\": string, \"reason\": string, \"contentBrief\": object}. "
                "Only recommend legitimate acquisition."
            )
            ai_text = self._ask_model(ai_prompt)
            self.state.last_thought = ai_text
            self.state.decision = {
                "action": "website_growth",
                "focus": "Increase legitimate traffic to the configured website.",
                "siteAnalysis": facts,
                "growthPlan": plan,
                "contentBrief": brief,
                "ai": ai_text,
                "updatedAt": now,
            }
            self.state.working_plan = [
                f"{item['action']}: {item['reason']}" for item in plan
            ]
            self._remember(
                "traffic_analysis",
                f"Analyzed {target}",
                {"facts": facts, "plan": plan},
            )
            self.last_analysis = now

        # Create attribution links and social drafts only for connected,
        # operator-authorized accounts. Draft creation is not fake traffic.
        if now - self.last_drafts >= 300:
            created = queue_growth_drafts(
                self.state,
                target,
                "timepressure-growth",
            )
            if created:
                self._remember(
                    "traffic_distribution",
                    f"Queued {created} authorized social draft(s).",
                    {"target": target, "created": created},
                )
            self.last_drafts = now

        self.store.save(self.state)
        return self.state.decision
