from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict
import re

@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    category: str
    description: str
    mode: str = "plan"
    risk: str = "low"

REGISTRY: Dict[str, Capability] = {}
HANDLERS: Dict[str, Callable[[dict], dict]] = {}

def register(capability: Capability):
    def deco(fn):
        REGISTRY[capability.id] = capability
        HANDLERS[capability.id] = fn
        fn.__name__ = capability.id.replace(".", "_")
        fn.__doc__ = capability.description
        return fn
    return deco

def _safe_plan(cap, context):
    return {
        "capability": cap.id, "name": cap.name, "category": cap.category,
        "status": "planned", "risk": cap.risk,
        "next_step": f"Evaluate {cap.name.lower()} against the current objective.",
        "guardrails": ["respect terms of service", "no deception", "no spam", "no unauthorized access"]
    }

_DEFINITIONS = {
"reasoning":"goal decomposition|constraint extraction|priority ranking|tradeoff analysis|assumption detection|ambiguity detection|question generation|plan synthesis|plan critique|alternative planning|dependency mapping|critical path analysis|risk scoring|confidence estimation|evidence grading|counterexample search|premortem analysis|postmortem analysis|decision matrix|expected value analysis|cost benefit analysis|time budget planning|resource allocation|bottleneck detection|next action selection",
"research":"web research|source comparison|source credibility scoring|fact extraction|fact checking|claim verification|change detection|competitor research|market research|keyword research|trend analysis|audience research|customer question mining|documentation lookup|technical research|pricing research|feature comparison|review synthesis|community sentiment scan|research brief generation|research gap detection|citation planning|evidence clustering|research summarization|research memory",
"daily":"task planning|calendar planning|reminder planning|shopping list planning|travel planning|study planning|meeting preparation|meeting agenda generation|follow-up drafting|note organization|document organization|deadline tracking|routine optimization|habit planning|personal checklist|email triage planning|message drafting|decision journaling|weekly review|daily review|goal tracking|time blocking|focus session planning|project breakdown|priority reset",
"writing":"email drafting|reply drafting|brief writing|proposal writing|report writing|documentation writing|technical explanation|plain language rewriting|professional rewriting|friendly rewriting|headline generation|hook generation|call to action writing|landing page copy|FAQ writing|case study writing|press release drafting|outreach drafting|script writing|video outline writing|social caption writing|newsletter writing|blog outline|blog drafting|copy quality review",
"brand":"brand positioning|brand naming|tagline generation|value proposition|brand voice|audience persona|brand story|messaging hierarchy|visual brief|creative brief|brand consistency check|brand differentiation|category mapping|offer design|product naming|campaign concept|content pillars|editorial calendar|brand FAQ|brand reputation monitoring|brand mention analysis|brand asset checklist|launch plan|relaunch plan|brand strategy review",
"seo":"technical seo audit|title optimization|meta description optimization|heading analysis|internal linking plan|schema planning|canonical review|indexability review|robots review|sitemap review|core web vitals checklist|image seo checklist|keyword clustering|search intent mapping|content gap analysis|serp opportunity analysis|featured snippet planning|local seo plan|international seo plan|backlink prospect research|linkable asset planning|seo content brief|content refresh plan|seo experiment design|seo reporting",
"content":"content ideation|content scoring|topic clustering|pillar page planning|short form planning|long form planning|video topic research|tutorial planning|comparison planning|case study planning|faq mining|evergreen content planning|newsjacking screening|content repurposing|content refresh|content calendar|content gap prioritization|content brief|content quality audit|content originality check|content readability check|content structure optimization|content distribution plan|content measurement plan|content archive",
"social":"social strategy|platform selection|post scheduling plan|thread planning|short video planning|carousel planning|community response drafting|comment response drafting|social listening|trend screening|creator outreach|collaboration brief|influencer shortlist|community calendar|social profile audit|bio optimization|profile conversion audit|hashtag research|social seo|content testing|engagement analysis|retention analysis|social experiment|repurposing workflow|social reporting",
"marketing":"funnel mapping|offer funnel planning|lead magnet planning|landing page audit|conversion audit|cta testing|pricing page audit|onboarding optimization|activation planning|retention planning|referral program planning|partnership planning|affiliate program planning|co marketing planning|campaign planning|campaign brief|audience segmentation|message testing|creative testing|channel attribution|utm planning|marketing dashboard design|growth experiment backlog|growth loop design|marketing review",
"analytics":"metric definition|kpi selection|event taxonomy|funnel analysis|cohort analysis|retention analysis|conversion analysis|traffic source analysis|campaign attribution|utm validation|anomaly detection|trend detection|experiment analysis|ab test planning|dashboard specification|report generation|weekly analytics review|growth scorecard|data quality audit|tracking plan|goal measurement|revenue attribution|content attribution|channel comparison|analytics summary",
"automation":"workflow design|task chaining|scheduled workflow planning|event trigger design|condition design|retry strategy|failure recovery|idempotency planning|queue planning|rate limit planning|approval gate design|human in the loop|dry run|simulation|execution preview|rollback planning|audit logging|run history|workflow testing|workflow optimization|tool selection|tool sequencing|parallel task planning|result validation|automation report",
"engineering":"codebase inspection|bug triage|error diagnosis|test planning|unit test generation|integration test planning|regression detection|refactor planning|dependency audit|performance review|security review|input validation review|api design|cli design|configuration design|logging design|observability plan|cache strategy|database planning|migration planning|release planning|versioning|changelog generation|documentation audit|developer onboarding",
"security":"threat modeling|permission review|secret detection plan|credential hygiene|least privilege review|input sanitization|output validation|rate limiting|abuse prevention|prompt injection defense|webhook validation|session safety|data minimization|privacy review|audit trail review|dependency vulnerability review|supply chain review|sandbox planning|network boundary review|safe browsing plan|account permission audit|consent check|policy compliance check|security checklist|incident response plan",
"finance":"budget planning|expense categorization|revenue model analysis|unit economics|pricing analysis|cash flow planning|break even analysis|scenario modeling|roi estimation|marketing roi|cost optimization|subscription audit|invoice checklist|financial dashboard plan|revenue forecast|expense forecast|budget variance analysis|savings plan|financial risk review|profitability analysis|offer economics|customer acquisition cost analysis|lifetime value analysis|margin analysis|finance summary",
"productivity":"focus prioritization|deep work planning|context switching reduction|work queue optimization|batching plan|template creation|shortcut discovery|checklist generation|process simplification|repetition detection|delegation planning|automation opportunity scan|meeting reduction plan|communication compression|status update generation|project health check|stale task detection|blocked task detection|next best action|workload balancing|energy aware planning|deadline recovery|backlog grooming|workspace organization|productivity review",
"customer":"customer journey mapping|support triage|support response drafting|faq extraction|feedback clustering|feature request clustering|complaint classification|churn signal analysis|customer health scoring|onboarding review|activation checklist|support knowledge base plan|self service plan|customer interview guide|survey design|survey synthesis|nps analysis|review response drafting|customer success plan|retention playbook|escalation planning|issue reproduction checklist|bug report drafting|customer insight report|voice of customer",
"sales":"lead qualification|prospect research|account research|sales brief|discovery questions|sales email drafting|follow up sequence|objection mapping|objection response drafting|demo plan|proposal outline|case study matching|account prioritization|pipeline review|deal risk scoring|next step recommendation|crm note drafting|sales dashboard plan|territory planning|partner prospecting|upsell opportunity analysis|cross sell opportunity analysis|renewal planning|sales experiment|sales review",
"creative":"creative ideation|concept expansion|concept selection|storyboard planning|visual direction|creative testing|thumbnail brief|ad concept|campaign concept|video hook|video structure|podcast outline|presentation outline|design critique|creative brief|moodboard brief|art direction|narrative structure|story arc|metaphor generation|name exploration|slogan exploration|creative variation|creative quality review|creative archive",
"operations":"process mapping|sop generation|checklist audit|vendor comparison|procurement planning|inventory planning|capacity planning|schedule optimization|handoff design|ownership mapping|sla planning|incident triage|operations dashboard|process bottleneck analysis|quality control plan|compliance checklist|document control|change management|launch operations|post launch review|operational risk review|business continuity plan|escalation matrix|runbook generation|operations summary"
}

assert len(_DEFINITIONS) == 20 and all(len(v.split("|")) == 25 for v in _DEFINITIONS.values())

def _make_handler(cap):
    def handler(context):
        return _safe_plan(cap, context)
    return handler

for category, raw in _DEFINITIONS.items():
    for index, name in enumerate(raw.split("|"), 1):
        cid = f"{category}.{index:02d}"
        cap = Capability(cid, name.title(), category, f"Use {name} to improve reasoning or execution for the current objective.")
        register(cap)(_make_handler(cap))

def list_capabilities(category=None):
    return [c for c in REGISTRY.values() if category is None or c.category == category]

def search_capabilities(query):
    terms = re.sub(r"[^a-z0-9 ]", " ", query.lower()).split()
    scored = []
    for c in REGISTRY.values():
        hay = f"{c.name.lower()} {c.description.lower()} {c.category.lower()}"
        score = sum(t in hay for t in terms)
        if score:
            scored.append((score, c))
    return [c for _, c in sorted(scored, key=lambda x: (-x[0], x[1].id))]

def run_capability(capability_id, context=None):
    if capability_id not in HANDLERS:
        raise KeyError(f"Unknown capability: {capability_id}")
    return HANDLERS[capability_id](context or {})
