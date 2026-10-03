from .models import PressureState

def calculate_pressure(now, state):
    if state.status == "dead":
        return state
    duration = max(1.0, state.deadline - state.cycle_started_at)
    elapsed = max(0.0, now - state.cycle_started_at)
    ratio = min(1.0, elapsed / duration)
    revenue_ratio = 1.0 if state.target_cents <= 0 else min(1.0, state.cycle_revenue_cents / state.target_cents)
    pressure = max(0.0, min(100.0, (ratio - revenue_ratio) * 100))
    status = "alive"
    if state.cycle_revenue_cents < state.target_cents:
        if now >= state.deadline:
            status = "dead"
        elif elapsed >= duration * 0.5:
            status = "critical"
        elif elapsed >= duration * 0.2:
            status = "warning"
    return PressureState(state.cycle_started_at, state.target_cents, state.cycle_revenue_cents, pressure, status, state.deadline, state.last_revenue_at)

def record_revenue(state, cents, now):
    if cents <= 0:
        raise ValueError("Revenue must be positive.")
    if state.status == "dead":
        raise ValueError("Agent is dead; reset the cycle explicitly.")
    next_total = state.cycle_revenue_cents + cents
    if next_total >= state.target_cents:
        duration = state.deadline - state.cycle_started_at
        return PressureState(now, state.target_cents, 0, 0, "alive", now + duration, now)
    return PressureState(state.cycle_started_at, state.target_cents, next_total, state.pressure, state.status, state.deadline, now)

def reset_cycle(state, now, cycle_ms):
    return PressureState(now, state.target_cents, 0, 0, "alive", now + cycle_ms)
