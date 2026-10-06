from __future__ import annotations
from dataclasses import dataclass, field
from .capabilities import REGISTRY, search_capabilities
from .policy import validate_objective, account_policy, marketing_policy

@dataclass
class SparkBot:
    pressure: float = 50.0
    memory: list[dict] = field(default_factory=list)

    def think(self, objective: str, context: dict | None = None):
        ok, reason = validate_objective(objective)
        if not ok:
            return {"status": "blocked", "reason": reason}
        matches = search_capabilities(objective)[:8] or list(REGISTRY.values())[:8]
        result = {
            "status": "ready",
            "agent": "Spark Bot",
            "objective": objective,
            "pressure": max(0, min(100, self.pressure)),
            "plan": [{"id": c.id, "name": c.name, "category": c.category} for c in matches],
            "reasoning": [
                "decompose objective", "select relevant capabilities",
                "check authorization and policy", "prefer measurable reversible actions",
                "execute only with required permissions", "verify outcome and learn",
            ],
            "context_keys": sorted((context or {}).keys()),
        }
        self.memory.append(result)
        return result

    def capabilities(self, category=None):
        return [c.__dict__ for c in REGISTRY.values() if category is None or c.category == category]

    def policies(self):
        return {"accounts": account_policy(), "marketing": marketing_policy()}

    def status(self):
        return {
            "agent": "Spark Bot", "version": "1.0.0",
            "capabilities": len(REGISTRY), "pressure": self.pressure,
            "memory_items": len(self.memory),
            "account_mode": "authorized accounts only",
            "marketing_mode": "legitimate/consented channels",
        }
