import crypto from 'node:crypto';
import { LitecoinRpc } from './litecoin.js';
import type { AgentConfig, PersistedState, PayoutEvent } from './types.js';

export function wallet(config: AgentConfig) { return new LitecoinRpc(config.litecoin); }

export async function payout(config: AgentConfig, amountLtc: number, address?: string) {
  if (!Number.isFinite(amountLtc) || amountLtc <= 0) throw new Error('LTC amount must be positive.');
  const target = address ?? config.litecoin.payoutAddress;
  if (!target) throw new Error('No payout address. Set LTC_PAYOUT_ADDRESS or pass an address.');
  const rpc = wallet(config);
  const balance = await rpc.getBalance();
  if (balance < amountLtc) throw new Error(`Insufficient LTC balance: ${balance} LTC available.`);
  const txid = await rpc.sendToAddress(target, amountLtc);
  return { txid, address: target, amountLtc };
}

export function usdToLtc(usd: number, ltcUsd: number) {
  if (!Number.isFinite(usd) || usd < 0) throw new Error('USD amount must be non-negative.');
  if (!Number.isFinite(ltcUsd) || ltcUsd <= 0) throw new Error('LTC/USD rate must be positive.');
  return usd / ltcUsd;
}

export function unpaidRevenue(state: PersistedState) {
  const paid = new Set(state.payouts.flatMap(p => p.revenueReferences));
  return state.revenue.filter(r => !paid.has(r.reference));
}

export function payoutEligible(state: PersistedState, minPayoutLtc: number, ltcUsd: number) {
  const revenueUsd = unpaidRevenue(state).reduce((sum, e) => sum + e.cents, 0) / 100;
  const ltc = usdToLtc(revenueUsd, ltcUsd);
  return { revenueUsd, ltc, eligible: ltc >= minPayoutLtc };
}

export async function payoutEarned(config: AgentConfig, state: PersistedState, ltcUsd: number) {
  const unpaid = unpaidRevenue(state);
  const revenueCents = unpaid.reduce((sum, e) => sum + e.cents, 0);
  if (!unpaid.length) throw new Error('No unpaid revenue.');
  const amountLtc = usdToLtc(revenueCents / 100, ltcUsd);
  if (amountLtc < config.litecoin.minPayoutLtc) throw new Error(`Payout is below minimum of ${config.litecoin.minPayoutLtc} LTC.`);
  const target = config.litecoin.payoutAddress;
  if (!target) throw new Error('LTC_PAYOUT_ADDRESS is required for payout-earned.');
  const result = await payout(config, amountLtc, target);
  const event: PayoutEvent = { id: crypto.randomUUID(), revenueReferences: unpaid.map(e => e.reference), revenueCents, ltcAmount: amountLtc, ltcUsdRate: ltcUsd, address: target, txid: result.txid, timestamp: Date.now() };
  state.payouts.push(event);
  return event;
}
