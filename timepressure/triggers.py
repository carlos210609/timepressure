import time
from dataclasses import dataclass

from .pressure import calculate_pressure


@dataclass(frozen=True)
class Trigger:
    name: str
    priority: int
    reason: str
    instruction: str


def evaluate(state, now=None):
    now = time.time() if now is None else now
    state.pressure = calculate_pressure(now, state.pressure)
    p = state.pressure
    left = max(0, p.deadline - now)
    triggers = []

    if p.status == "dead":
        return [Trigger(
            "dead", 1000,
            "The cycle missed its deadline.",
            "Stop spending resources; wait for an explicit reset.",
        )]

    if left <= 60 and p.cycle_revenue_cents < p.target_cents:
        triggers.append(Trigger(
            "deadline_imminent", 950, f"Only {int(left)} seconds remain.",
            "Prefer one short, measurable, legitimate action.",
        ))
    elif left <= 300 and p.cycle_revenue_cents < p.target_cents:
        triggers.append(Trigger(
            "deadline_near", 850, f"Only {int(left)} seconds remain.",
            "Abandon slow research and choose a reversible high-value action.",
        ))

    if p.pressure >= 80:\n        triggers.append(Trigger(\n            "red_zone", 900, f"Pressure is {p.pressure:.1f}% with {int(left)} seconds left.",\n            "Stop broad exploration. Select the fastest legitimate path with measurable progress and keep independent safe work running in parallel.",\n        ))\n\n    if p.status == "critical":
        triggers.append(Trigger(
            "critical_pressure", 800, f"Pressure is {p.pressure:.1f}%.",
            "Switch to fast time-to-value actions.",
        ))
    elif p.status == "warning":
        triggers.append(Trigger(
            "warning_pressure", 600, f"Pressure is {p.pressure:.1f}%.",
            "Shorten research and prioritize clear monetization paths.",
        ))

    cycle_revenue = [x for x in state.revenue if x.timestamp >= p.cycle_started_at]
    if not cycle_revenue and now - p.cycle_started_at >= 1800:
        triggers.append(Trigger(
            "no_revenue_30m", 700, "No revenue recorded for 30 minutes.",
            "Change strategy and research a different legitimate revenue path.",
        ))

    if not state.browser_history:
        triggers.append(Trigger(
            "no_browser_history", 250, "Browser has not been used.",
            "If configured, research an allowed opportunity before guessing.",
        ))

    triggers.sort(key=lambda x: x.priority, reverse=True)
    return triggers


def compact(triggers, limit=5):
    return [
        {
            "name": t.name,
            "priority": t.priority,
            "reason": t.reason,
            "instruction": t.instruction,
        }
        for t in triggers[:limit]
    ]
