import json
import time
import urllib.request
import uuid
from .models import MemoryEvent
from .pressure import calculate_pressure
from .tools import TOOLS, run_tool

class Agent:
    def __init__(self, config, store, state):
        self.config, self.store, self.state = config, store, state

    def _remember(self, kind, text, metadata=None):
        self.store.add_memory(self.state, MemoryEvent(str(uuid.uuid4()), kind, text, time.time(), metadata or {}))

    def _ask_model(self, prompt):
        payload = json.dumps({
            "model": self.config.model,
            "instructions": "You are a cautious autonomous agent. Return concise JSON only.",
            "input": prompt,
            "store": False,
        }).encode()
        request = urllib.request.Request(
            self.config.base_url.rstrip("/") + "/responses",
            payload,
            {"Content-Type": "application/json", "Authorization": "Bearer " + self.config.api_key},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read())
        if data.get("output_text"):
            return data["output_text"]
        for item in data.get("output", []):
            for part in item.get("content", []):
                if part.get("type") in ("output_text", "text") and part.get("text"):
                    return part["text"]
        return ""

    def tick(self):
        self.state.pressure = calculate_pressure(time.time(), self.state.pressure)
        self.store.save(self.state)
        if self.state.pressure.status == "dead":
            return
        if not self.config.api_key:
            self._remember("observation", "No OPENAI_API_KEY configured.")
            return
        p = self.state.pressure
        prompt = (
            "You are TimePressure, an autonomous economic agent.\n"
            f"Goal: {self.state.working_goal}\n"
            f"Pressure: {p.pressure:.1f}%\n"
            f"Cycle revenue: USD {p.cycle_revenue_cents/100:.2f}\n"
            f"Target: USD {p.target_cents/100:.2f}\n"
            f"Deadline: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(p.deadline))}\n"
            "Choose one legitimate, legal, non-deceptive action that can create value. "
            "Never fabricate revenue, make purchases, gamble, evade controls, or expose secrets.\n"
            f"Available tools: {json.dumps(TOOLS)}\n"
            'Return JSON: {"action":"tool name or none","input":"...","rationale":"..."}'
        )
        try:
            text = self._ask_model(prompt)
            self.state.last_thought = text
            self._remember("action", text, {"pressure": p.pressure})
            plan = json.loads(text)
            action = plan.get("action")
            if action in TOOLS:
                output = run_tool(action, str(plan.get("input", "")), self.config)
                self._remember("observation", f"{action}: {output}")
        except Exception as exc:
            self._remember("error", str(exc))
