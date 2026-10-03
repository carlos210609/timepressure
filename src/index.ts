import { loadConfig } from './config.js';
import { Store } from './store.js';
import { Agent } from './agent.js';
import { calculatePressure, recordRevenue, resetCycle } from './pressure.js';
import crypto from 'node:crypto';
import { wallet, payout, payoutEarned, usdToLtc } from './wallet.js';
import { login, status as authStatus, logout } from './auth.js';

const config = loadConfig();
const store = new Store(config.dataDir);
const state = await store.init();
state.pressure.targetCents = config.targetCents;
if (state.pressure.status !== 'dead') state.pressure.deadline = state.pressure.cycleStartedAt + config.cycleMs;
const agent = new Agent(config, store, state);

function usage() {
  console.log(`TimePressure

Commands:
  run
  status
  pressure
  revenue add <USD> [--source name] [--reference id]
  wallet balance
  wallet address [label]
  wallet payout <LTC> [address]
  wallet quote <USD> <LTC/USD>
  reset
  doctor`);
}

async function main() {
  const [cmd, sub, amount, ...rest] = process.argv.slice(2);
  if (!cmd || cmd === 'help') return usage();
  if (cmd === 'login' && sub === 'status') return authStatus();
  if (cmd === 'login') return login();
  if (cmd === 'logout') return logout();

  if (cmd === 'status' || cmd === 'pressure') {
    state.pressure = calculatePressure(Date.now(), state.pressure);
    await store.save(state);
    console.log(JSON.stringify({
      status: state.pressure.status,
      pressure: `${state.pressure.pressure.toFixed(1)}%`,
      cycleRevenue: `$${(state.pressure.cycleRevenueCents / 100).toFixed(2)}`,
      target: `$${(state.pressure.targetCents / 100).toFixed(2)}`,
      deadline: new Date(state.pressure.deadline).toISOString()
    }, null, 2));
    return;
  }

  if (cmd === 'revenue' && sub === 'add') {
    const usd = Number(amount);
    if (!Number.isFinite(usd) || usd <= 0) throw new Error('Amount must be positive.');
    const sourceIndex = rest.indexOf('--source');
    const refIndex = rest.indexOf('--reference');
    const source = sourceIndex >= 0 ? rest[sourceIndex + 1] : 'manual';
    const reference = refIndex >= 0 ? rest[refIndex + 1] : crypto.randomUUID();
    if (!source || !reference) throw new Error('Invalid source/reference.');
    if (state.revenue.some(r => r.reference === reference)) throw new Error('Duplicate revenue reference.');
    const now = Date.now();
    const event = { id: crypto.randomUUID(), cents: Math.round(usd * 100), source, reference, timestamp: now };
    await store.addRevenue(state, event);
    state.pressure = recordRevenue(state.pressure, event.cents, now);
    await store.save(state);
    if (config.litecoin.autoPayout) {
      if (!config.litecoin.usdRate) throw new Error('LTC_USD_RATE is required when LTC_AUTO_PAYOUT=true.');
      const payoutEvent = await payoutEarned(config, state, config.litecoin.usdRate);
      await store.save(state);
      console.log(JSON.stringify({ revenue: event, automaticPayout: payoutEvent }, null, 2));
      return;
    }
    console.log(`Recorded ${(event.cents / 100).toFixed(2)} from ${source}. Status: ${state.pressure.status}`);
    return;
  }

  if (cmd === 'reset') {
    state.pressure = resetCycle(state.pressure, Date.now(), config.cycleMs);
    await store.save(state);
    console.log('Cycle reset.');
    return;
  }

  if (cmd === 'wallet' && sub === 'balance') {
    console.log(`${await wallet(config).getBalance()} LTC`);
    return;
  }
  if (cmd === 'wallet' && sub === 'address') {
    console.log(await wallet(config).getNewAddress(amount || 'timepressure'));
    return;
  }
  if (cmd === 'wallet' && sub === 'payout-earned') {
    const rate = Number(amount);
    if (!Number.isFinite(rate) || rate <= 0) throw new Error('Usage: wallet payout-earned <LTC/USD>');
    const event = await payoutEarned(config, state, rate);
    await store.save(state);
    console.log(JSON.stringify(event, null, 2));
    return;
  }
  if (cmd === 'wallet' && sub === 'payout') {
    const ltc = Number(amount);
    console.log(JSON.stringify(await payout(config, ltc, rest[0]), null, 2));
    return;
  }
  if (cmd === 'wallet' && sub === 'quote') {
    const usd = Number(amount), rate = Number(rest[0]);
    console.log(JSON.stringify({ usd, ltcUsd: rate, ltc: usdToLtc(usd, rate) }, null, 2));
    return;
  }
  if (cmd === 'doctor') {
    console.log(JSON.stringify({
      node: process.version,
      dataDir: config.dataDir,
      modelConfigured: Boolean(config.apiKey),
      networkEnabled: config.allowNetwork,
      target: `$${(config.targetCents / 100).toFixed(2)}`,
      cycleMs: config.cycleMs,
      litecoinRpcConfigured: Boolean(config.litecoin.rpcUrl && config.litecoin.rpcUser && config.litecoin.rpcPassword),
      payoutAddressConfigured: Boolean(config.litecoin.payoutAddress),
      autoPayout: config.litecoin.autoPayout
    }, null, 2));
    return;
  }
  if (cmd === 'run') {
    console.log('TimePressure running. Ctrl+C to stop.');
    const loop = async (): Promise<void> => {
      await agent.tick();
      const s = agent.getState().pressure;
      console.log(`[${new Date().toISOString()}] ${s.status} pressure=${s.pressure.toFixed(1)}% revenue=$${(s.cycleRevenueCents / 100).toFixed(2)}`);
      if (s.status === 'dead') {
        console.log('DEAD: revenue target was missed.');
        process.exitCode = 2;
        return;
      }
      setTimeout(() => { void loop(); }, config.tickMs);
    };
    await loop();
    return;
  }
  usage();
}

main().catch(error => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
