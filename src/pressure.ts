import type {AgentStatus,PressureState} from './types.js';
export function calculatePressure(now:number,state:PressureState):PressureState{
 if(state.status==='dead')return state;
 const elapsed=Math.max(0,now-state.cycleStartedAt),duration=state.deadline-state.cycleStartedAt;
 const ratio=Math.min(1,elapsed/duration),revenueRatio=state.targetCents<=0?1:Math.min(1,state.cycleRevenueCents/state.targetCents);
 const pressure=Math.max(0,Math.min(100,(ratio-revenueRatio)*100));
 let status:AgentStatus='alive';
 if(state.cycleRevenueCents>=state.targetCents)status='alive'; else if(elapsed>=duration*.5)status='warning'; else if(elapsed>=duration*.2)status='critical';
 if(now>=state.deadline&&state.cycleRevenueCents<state.targetCents)status='dead';
 return{...state,pressure,status};
}
export function recordRevenue(state:PressureState,cents:number,now:number):PressureState{
 if(!Number.isFinite(cents)||cents<=0)throw new Error('Revenue must be a positive finite amount in cents.');
 if(state.status==='dead')throw new Error('Agent is dead; start a new cycle explicitly.');
 const next=state.cycleRevenueCents+cents;
 if(next>=state.targetCents)return{...state,cycleStartedAt:now,cycleRevenueCents:0,pressure:0,status:'alive',lastRevenueAt:now,deadline:now+(state.deadline-state.cycleStartedAt)};
 return{...state,cycleRevenueCents:next,lastRevenueAt:now};
}
export function resetCycle(state:PressureState,now:number,cycleMs:number):PressureState{return{...state,cycleStartedAt:now,cycleRevenueCents:0,pressure:0,status:'alive',deadline:now+cycleMs}}
