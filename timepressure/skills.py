"""Compact skill router for TimePressure.

Skills are procedural: each one tells the agent what to optimize, what evidence to seek,
and when to stop. They are intentionally short so they add intelligence without making
every model call expensive.
"""

SKILLS = {
    "website_audit": {
        "goal": "Find one concrete, publicly verifiable website problem that can become a paid fixed-scope audit.",
        "first_action": "inspect a candidate site and collect 3 evidence-backed issues",
        "success_signal": "a specific audit deliverable and a legitimate prospect/contact path",
        "stop_when": "the evidence is sufficient for a concise offer",
    },
    "seo_audit": {
        "goal": "Find high-impact technical SEO issues with clear evidence.",
        "first_action": "inspect one public site for indexability, metadata, performance or structure problems",
        "success_signal": "3+ reproducible issues with a clear business impact",
        "stop_when": "the findings can be packaged into a fixed-price audit",
    },
    "bug_fixing": {
        "goal": "Deliver one narrowly scoped programming fix with clear acceptance criteria.",
        "first_action": "identify a small reproducible bug and its expected behavior",
        "success_signal": "a minimal patch or verified diagnosis",
        "stop_when": "the acceptance criteria are demonstrably met",
    },
    "code_review": {
        "goal": "Produce a concise, evidence-backed code review that saves the client time or reduces risk.",
        "first_action": "inspect the smallest relevant code surface",
        "success_signal": "specific actionable findings with severity and reproduction/evidence",
        "stop_when": "the review has enough evidence to deliver",
    },
    "copy_editing": {
        "goal": "Improve client-provided copy without inventing claims.",
        "first_action": "identify the highest-impact clarity or conversion problems",
        "success_signal": "a before/after deliverable with concrete improvements",
        "stop_when": "the requested copy scope is complete",
    },
    "template_pack": {
        "goal": "Create a small genuinely useful digital asset that can be sold legitimately.",
        "first_action": "choose one narrow audience and one painful repetitive task",
        "success_signal": "a usable asset plus a clear listing and price",
        "stop_when": "the smallest sellable version is complete",
    },
    "lead_research": {
        "goal": "Build a small, permission-aware prospect list from public business information.",
        "first_action": "identify 3 relevant businesses matching the service criteria",
        "success_signal": "qualified prospects with public contact paths and a personalized reason to reach out",
        "stop_when": "there are enough qualified prospects for a focused outreach batch",
    },
}


def get_skill(strategy_id: str) -> dict:
    return SKILLS.get(strategy_id, {
        "goal": "Choose the smallest legitimate action with measurable evidence.",
        "first_action": "inspect the highest-value current opportunity",
        "success_signal": "new evidence that improves the next decision",
        "stop_when": "the next decision is obvious",
    })


def compact_skill_context(strategy_id: str) -> str:
    s = get_skill(strategy_id)
    return (
        f"Skill={strategy_id}; goal={s['goal']}; first_action={s['first_action']}; "
        f"success_signal={s['success_signal']}; stop_when={s['stop_when']}"
    )
