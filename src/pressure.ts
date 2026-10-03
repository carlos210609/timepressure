import type { AgentStatus, PressureState } from './types.js';

export function calculatePressure(now: number, state: PressureState): PressureState {
  if (state.status === 'dead') return state;
  const elapsed = Math.max(0, now - state.cycleStartedAt);
  const ratio = Math.min(1, elapsed / (state.deadline - state.cycleStartedAt));
  const revenueRatio = state.targetCents <= 0 ? 1 : Math.min(1, state.cycleRevenueCents / state.targetCents);
  const pressure = Math.max(0, Math.min(100, (ratio - revenueRatio) * 100));
  let status: AgentStatus = 'alive';
  if (state.cycleRevenueCents >= state.targetCents) status = 'alive';
  else if (elapsed >= (state.deadline - state.cycleStartedAt) * 0.2) status = 'critical';
  else if (elapsed >= state.cycleStartedAt + (state.deadline - state.cycleStartedAt) / 2) status = 'warning';
  if (now >= state.deadline && state.cycleRevenueCents < state.targetCents) status = 'dead';
  return { ...state, pressure, status };
}

export function recordRevenue(state: PressureState, cents: number, now: number): PressureState {
  if (!Number.isFinite(cents) || cents <= 0) throw new Error('Revenue must be a positive finite amount in cents.');
  if (state.status === 'dead') throw new Error('Agent is dead; start a new cycle explicitly.');
  const nextRevenue = state.cycleRevenueCents + cents;
  if (nextRevenue >= state.targetCents) {
    return { ...state, cycleStartedAt: now, cycleRevenueCents: 0, pressure: 0, status: 'alive', lastRevenueAt: now, deadline: now + (state.deadline - state.cycleStartedAt) };
  }
  return { ...state, cycleRevenueCents: nextRevenue, lastRevenueAt: now };
}

export function resetCycle(state: PressureState, now: number, cycleMs: number): PressureState {
  return { ...state, cycleStartedAt: now, cycleRevenueCents: 0, pressure: 0, status: 'alive', deadline: now + cycleMs };
}
