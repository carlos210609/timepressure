from __future__ import annotations
from dataclasses import dataclass, field
from time import perf_counter
from .capabilities import REGISTRY, Skill, search_skills
from .executor import SkillExecutor
from .policy import validate_objective, account_policy, marketing_policy
from .telemetry import TelemetryStore, SkillTelemetry

@dataclass
class SparkBot:
    pressure: float = 50.0
    memory: list[dict] = field(default_factory=list)
    telemetry: TelemetryStore = field(default_factory=TelemetryStore)
    executor: SkillExecutor = field(default_factory=SkillExecutor)

    def discover(self, objective: str, limit: int = 20) -> list[Skill]:
        return search_skills(objective, limit)

    def think(self, objective: str, context: dict | None = None):
        ok, reason = validate_objective(objective)
        if not ok:
            return {"status": "blocked", "reason": reason}
        matches = self.discover(objective, 8) or list(REGISTRY.values())[:8]
        plan = [{"id": s.id, "name": s.name, "category": s.category,
                 "risk_level": s.risk_level, "permissions": list(s.permissions),
                 "prerequisites": list(s.prerequisites)} for s in matches]
        result = {"status": "ready", "agent": "Spark Bot", "objective": objective,
                  "pressure": max(0, min(100, self.pressure)), "execution_mode": "DRY_RUN",
                  "plan": plan,
                  "pipeline": ["intent","goal","skill_search","ranking","dependency_check",
                               "permission_check","execution","verification","telemetry","learning"]}
        self.memory.append({"type": "mission", "objective": objective, "plan": plan})
        return result

    def run_skill(self, skill_id, objective, mode="DRY_RUN", context=None):
        started = perf_counter()
        out = self.executor.execute(skill_id, objective, mode=mode, context=context)
        self.telemetry.record(SkillTelemetry(skill_id, out.status == "verified",
                                             (perf_counter()-started)*1000))
        self.memory.append({"skill": skill_id, "objective": objective,
                            "status": out.status, "verification": out.verification})
        return {"skill_id": out.skill_id, "status": out.status, "result": out.result,
                "evidence": out.evidence, "verification": out.verification}

    def capabilities(self, category=None):
        return [s.to_dict() for s in REGISTRY.values()
                if category is None or s.category == category]

    def policies(self):
        return {"accounts": account_policy(), "marketing": marketing_policy()}

    def status(self):
        return {"agent": "Spark Bot", "version": "2.0.0", "skills": len(REGISTRY),
                "domains": 100, "skills_per_domain": 15, "pressure": self.pressure,
                "memory_items": len(self.memory), "telemetry": self.telemetry.summary(),
                "execution_modes": ["SIMULATION","DRY_RUN","PRODUCTION"]}
