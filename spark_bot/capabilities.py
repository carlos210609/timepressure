from __future__ import annotations
"""Production skill registry for Spark Bot.

The registry is data-driven: skills are metadata, while execution is delegated to
shared primitives. This keeps 1,500+ skills composable without 1,500 copies of code.
"""
from dataclasses import asdict, dataclass, field
import re
from typing import Any

RISK_LEVELS = {"low", "medium", "high", "critical"}
PERMISSIONS = {"READ", "WRITE", "PUBLISH", "COMMUNICATE", "FINANCIAL", "ACCOUNT", "ADMIN"}

@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    purpose: str
    category: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ("READ",)
    risk_level: str = "low"
    prerequisites: tuple[str, ...] = ()
    success_conditions: tuple[str, ...] = ("structured_result_exists",)
    failure_conditions: tuple[str, ...] = ("execution_error", "verification_failed")
    verification_method: str = "result_schema"
    cost_estimate: str = "unknown"
    latency_estimate: str = "unknown"
    version: str = "1.0.0"
    enabled: bool = True
    telemetry: bool = True

    def __post_init__(self):
        if self.risk_level not in RISK_LEVELS:
            raise ValueError(f"invalid risk level: {self.risk_level}")
        if any(p not in PERMISSIONS for p in self.permissions):
            raise ValueError("invalid permission")
        if self.id.count(".") != 1:
            raise ValueError(f"invalid skill id: {self.id}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

REGISTRY: dict[str, Skill] = {}

# 100 domains × 15 operational slots. The canonical names can be replaced/extended
# without changing the executor. Slots are deliberately unique and machine-addressable.
DOMAINS = [
"core-intelligence","reasoning","planning","decision-making","memory","knowledge",
"research","web-intelligence","browser-operations","task-execution","self-correction",
"meta-intelligence","marketing-strategy","branding","customer-research","market-analysis",
"competitive-intelligence","instagram","reels","stories","social-content","tiktok","youtube",
"x-microblogging","linkedin","facebook","threads","pinterest","reddit","community",
"content-strategy","copywriting","storytelling","seo","local-seo","paid-advertising","meta-ads",
"google-ads","email-marketing","crm","sales","lead-generation","outbound","sales-enablement",
"customer-success","retention","referral","influencer-marketing","affiliate-marketing",
"partnerships","growth","cro","funnels","product-marketing","pricing","ecommerce","marketplaces",
"content-distribution","viral-content","analytics","data-science","experimentation","forecasting",
"revenue","finance","project-management","automation","api","integrations","crm-communication",
"customer-support","conversational-ai","multilingual","creative-direction","video","design",
"website","software-engineering","git","devops","security","privacy","compliance",
"account-management","credentials","observability","notifications","scheduling","reporting",
"executive-intelligence","opportunity-detection","trend-intelligence","reputation",
"crisis-management","productivity","knowledge-work","file-intelligence","learning",
"self-optimization","autonomous-super-agent"
]

assert len(DOMAINS) == 100

# Canonical 15-slot taxonomy. Domain-specific names can be mapped through this table.
SLOT_NAMES = [
"Intent Detection","Goal Understanding","Context Interpretation","Constraint Detection",
"Requirement Extraction","Ambiguity Detection","Priority Detection","Urgency Detection",
"Outcome Definition","Success Criteria Generation","Task Classification","Complexity Estimation",
"Risk Estimation","Resource Estimation","Mission Initialization"
]

def _display_name(domain: str, slot: str) -> str:
    prefix = domain.replace("-", " ").title()
    return f"{prefix} — {slot}"

def _category(domain: str) -> str:
    return domain.replace("-", "_")

def _risk(domain: str, slot_index: int) -> str:
    if domain in {"security","privacy","credentials","account-management","compliance"} and slot_index >= 12:
        return "high"
    if domain in {"finance","paid-advertising","meta-ads","google-ads","autonomous-super-agent"} and slot_index >= 10:
        return "medium"
    return "low"

def _permissions(domain: str, slot_index: int) -> tuple[str, ...]:
    if domain in {"security","privacy","credentials","compliance"}:
        return ("READ",)
    if slot_index in {14, 15}:
        return ("READ","WRITE")
    return ("READ",)

def build_registry() -> dict[str, Skill]:
    registry: dict[str, Skill] = {}
    for d, domain in enumerate(DOMAINS, 1):
        for s, slot in enumerate(SLOT_NAMES, 1):
            sid = f"{d:03d}.{s:02d}"
            prereq = ()
            if s > 1:
                prereq = (f"{d:03d}.{s-1:02d}",)
            skill = Skill(
                id=sid,
                name=_display_name(domain, slot),
                purpose=f"Operationally perform {slot.lower()} for the {domain.replace('-', ' ')} domain.",
                category=_category(domain),
                inputs=("objective","context"),
                outputs=("result","evidence"),
                tools=("shared_primitives",),
                permissions=_permissions(domain, s),
                risk_level=_risk(domain, s),
                prerequisites=prereq,
                success_conditions=("result_schema_valid","verification_passed"),
                failure_conditions=("tool_error","permission_denied","verification_failed"),
                verification_method="structured_result_and_evidence",
                cost_estimate="provider-dependent",
                latency_estimate="provider-dependent",
            )
            registry[sid] = skill
    return registry

REGISTRY = build_registry()
assert len(REGISTRY) == 1500, f"expected 1500 skills, got {len(REGISTRY)}"

def list_skills(category: str | None = None) -> list[dict[str, Any]]:
    skills = REGISTRY.values()
    if category:
        skills = (s for s in skills if s.category == category)
    return [s.to_dict() for s in skills]

def search_skills(query: str, limit: int = 20) -> list[Skill]:
    terms = re.sub(r"[^a-z0-9À-ÿ ]", " ", query.lower()).split()
    scored: list[tuple[float, Skill]] = []
    for skill in REGISTRY.values():
        hay = f"{skill.name.lower()} {skill.purpose.lower()} {skill.category.lower()}"
        score = sum(1 for term in terms if term in hay)
        if score:
            scored.append((score, skill))
    return [s for _, s in sorted(scored, key=lambda x: (-x[0], x[1].id))[:limit]]

def get_skill(skill_id: str) -> Skill:
    try:
        return REGISTRY[skill_id]
    except KeyError:
        raise KeyError(f"unknown skill: {skill_id}") from None
