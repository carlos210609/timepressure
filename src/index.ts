import { loadConfig } from './config.js';
import { Store } from './store.js';
import { Agent } from './agent.js';
import { calculatePressure, recordRevenue, resetCycle } from './pressure.js';
import crypto from 'node:crypto';
import { wallet, payout, usdToLtc } from './wallet.js';

const config = loadConfig();
const store = new Store(config.dataDir);
const state = await store.init();
state.pressure.targetCents = config.targetCents;
state.pressure.deadline = state.pressure.cycleStartedAt + config.cycleMs;
const agent = new Agent(config, store, state);

function usage() { console.log(`TimePressure\n\nCommands:\n  run\n  status\n  pressure\n  revenue add <USD> [--source name] [--reference id]\n  wallet balance\n  wallet address [label]\n  wallet payout <LTC> [address]\n  wallet quote <USD> <LTC/USD>\n  reset\n  doctor`); }

const [cmd, sub, amount, ...rest] = process.argv.slice(2);
if (!cmd || cmd === 'help') usage();
else if (cmd === 'status' || cmd === 'pressure') {
  state.pressure = calculatePressure(Date.now(), state.pressure); await store.save(state);
  console.log(JSON.stringify({ status: state.pressure.status, pressure: `${state.pressure.pressure.toFixed(1)}%`, cycleRevenue: `$${(state.pressure.cycleRevenueCents/100).toFixed(2)}`, target: `$${(state.pressure.targetCents/100).toFixed(2)}`, deadline: new Date(state.pressure.deadline).toISOString() }, null, 2));
} else if (cmd === 'revenue' && sub === 'add') {
  const usd = Number(amount); if (!Number.isFinite(usd) || usd <= 0) throw new Error('Amount must be positive.');
  const sourceIndex = rest.indexOf('--source'); const refIndex = rest.indexOf('--reference');
  const source = sourceIndex >= 0 ? rest[sourceIndex+1] : 'manual'; const reference = refIndex >= 0 ? rest[refIndex+1] : crypto.randomUUID();
  if (state.revenue.some(r => r.reference === reference)) throw new Error('Duplicate revenue reference.');
  const now = Date.now(); const event = { id: crypto.randomUUID(), cents: Math.round(usd*100), source, reference, timestamp: now };
  await store.addRevenue(state, event); state.pressure = recordRevenue(state.pressure, event.cents, now); await store.save(state);
  console.log(`Recorded $${(event.cents/100).toFixed(2)} from ${source}. Status: ${state.pressure.status}`);
} else if (cmd === 'reset') { state.pressure = resetCycle(state.pressure, Date.now(), config.cycleMs); await store.save(state); console.log('Cycle reset.'); }
else if (cmd === 'wallet' && sub === 'balance') { const b = await wallet(config).getBalance(); console.log(`${b} LTC`); }
else if (cmd === 'wallet' && sub === 'address') { const a = await wallet(config).getNewAddress(amount || 'timepressure'); console.log(a); }
else if (cmd === 'wallet' && sub === 'payout') { const ltc = Number(amount); const result = await payout(config, ltc, rest[0]); console.log(JSON.stringify(result, null, 2)); }
else if (cmd === 'wallet' && sub === 'quote') { const usd = Number(amount); const rate = Number(rest[0]); console.log(JSON.stringify({ usd, ltcUsd: rate, ltc: usdToLtc(usd, rate) }, null, 2)); }
else if (cmd === 'doctor') { console.log(JSON.stringify({ node: process.version, dataDir: config.dataDir, modelConfigured: Boolean(config.apiKey), networkEnabled: config.allowNetwork, target: `$${(config.targetCents/100).toFixed(2)}`, cycleMs: config.cycleMs }, null, 2)); }
else if (cmd === 'run') {
  console.log('TimePressure running. Ctrl+C to stop.');
  const loop = async () => { await agent.tick(); const s = agent.getState().pressure; console.log(`[${new Date().toISOString()}] ${s.status} pressure=${s.pressure.toFixed(1)}% revenue=$${(s.cycleRevenueCents/100).toFixed(2)}`); if (s.status === 'dead') { console.log('DEAD: revenue target was missed.'); process.exitCode = 2; return; } setTimeout(loop, config.tickMs); };
  await loop();
} else usage();
