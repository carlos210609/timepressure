"""Generated 10,000-item engineering backlog for TimePressure.

The backlog is intentionally generated from deterministic templates so the
repository stays maintainable instead of storing thousands of duplicate
source files. Run: python3 timepressure.py backlog export
"""
from __future__ import annotations

AREAS = [
    "Architecture", "Autonomy", "Marketplace", "Learning", "Revenue",
    "Dashboard", "Security", "Performance", "Testing", "Operations",
    "UX", "Documentation", "Resilience", "Observability", "Governance",
    "Data", "Automation", "Planning", "Prioritization", "Reliability",
]

SUBJECTS = [
    "the agent", "the task runner", "the marketplace selector",
    "the active connector", "the scoring engine", "the risk engine",
    "the revenue engine", "the memory system", "the decision history",
    "the dashboard", "the local API", "the CLI", "local storage",
    "logs", "metrics", "authentication", "permissions", "the scheduler",
    "retry handling", "the circuit breaker", "dry-run mode", "automatic mode",
    "manual mode", "alerts", "CI", "deployment", "failure recovery",
    "secret protection", "result collection", "profit calculation",
    "daily projection", "hourly value calculation", "task filtering",
    "opportunity selection", "confidence scoring", "risk analysis",
    "historical learning", "pattern detection", "anomaly detection",
    "observability", "performance", "configuration", "compatibility",
]

ACTIONS = [
    "refactor {x} to separate responsibilities",
    "add input validation to {x}",
    "add structured logging for {x}",
    "add unit tests for {x}",
    "add integration tests for {x}",
    "measure execution time of {x}",
    "add a bounded retry policy to {x}",
    "add a circuit breaker around {x}",
    "add a confidence score for {x}",
    "add a risk limit for {x}",
    "add a daily limit for {x}",
    "record the reason for decisions involving {x}",
    "compare alternatives before {x}",
    "add a safe fallback for {x}",
    "record the outcome of {x}",
    "calculate the success rate of {x}",
    "detect recurring failures in {x}",
    "detect recurring successes in {x}",
    "compare old and new strategies for {x}",
    "create a compact memory entry for {x}",
    "calculate net revenue for {x}",
    "calculate revenue per hour for {x}",
    "calculate cost per execution for {x}",
    "calculate ROI for {x}",
    "separate estimated revenue from verified revenue in {x}",
    "add a dashboard indicator for {x}",
    "add historical metrics for {x}",
    "add an audit trail for {x}",
    "protect credentials used by {x}",
    "add rate limiting to {x}",
    "add a dry-run mode for {x}",
    "add a diagnostic command for {x}",
    "add a health check for {x}",
    "create a regression test for {x}",
    "create a failure-recovery test for {x}",
    "improve error messages for {x}",
    "reduce unnecessary calls in {x}",
    "add safe caching around {x}",
    "document the operational procedure for {x}",
    "add telemetry for {x}",
    "add a maintenance routine for {x}",
]

def items(limit=10000):
    out = []
    i = 1
    for area in AREAS:
        for subject in SUBJECTS:
            for action in ACTIONS:
                if i > limit:
                    return out
                out.append({
                    "id": i,
                    "area": area,
                    "action": action.format(x=subject),
                    "status": "planned",
                    "priority": "normal",
                })
                i += 1
    return out[:limit]

def markdown(limit=10000):
    rows = ["# TimePressure — 10,000-item engineering backlog", "",
            "Generated deterministically from the project's backlog taxonomy.", ""]
    for item in items(limit):
        rows.append(f'{item["id"]:05d}. **[{item["area"]}]** {item["action"]}')
    return "\n".join(rows) + "\n"
