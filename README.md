# TimePressure

**TimePressure** is an open-source autonomous-agent runtime inspired by economic-survival agents, but with a different core mechanic: **time creates pressure**.

The default rule is simple:

> The agent has one hour to record at least **$0.01** of verified revenue. If it misses the deadline, the runtime transitions to `dead`.

Revenue is recorded through an explicit ledger interface. The runtime does not fake revenue, silently charge users, or infer revenue from model output.

## Architecture

- **Agent loop** — observe → plan → act → learn.
- **Pressure engine** — converts elapsed time into survival pressure.
- **Revenue ledger** — explicit revenue events with idempotency references.
- **Persistent state** — JSON state plus bounded memory events.
- **Tool registry** — local shell, file and HTTP tools.
- **Policy engine** — blocks selected dangerous commands and unsafe paths.
- **CLI** — `run`, `status`, `pressure`, `revenue`, `wallet`, `doctor`.

## Quick start

```bash
npm install
cp .env.example .env
npm run build
node dist/index.js status
node dist/index.js run
```

For model-backed operation, configure `OPENAI_API_KEY`. Without it, the runtime remains in deterministic demo mode.

## Revenue

For testing:

```bash
node dist/index.js revenue add 0.01 --source demo --reference demo-001
```

The same reference cannot be recorded twice.

## Litecoin

TimePressure can connect to a local Litecoin Core wallet through JSON-RPC. It does **not** store private keys; signing remains inside Litecoin Core.

```bash
node dist/index.js wallet balance
node dist/index.js wallet address
node dist/index.js wallet quote 1 80
node dist/index.js wallet payout 0.001
```

`wallet quote` uses a user-supplied LTC/USD rate. `wallet payout` sends real LTC. Keep `LTC_AUTO_PAYOUT=false`; automatic payout is not implemented in this version.

Never commit RPC passwords, wallet backups, seed phrases, or private keys.

## Safety

This is an experimental autonomous-agent runtime. Do not give it unrestricted credentials, payment keys, production access, or access to systems you do not control.

## License

MIT
