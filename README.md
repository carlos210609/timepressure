# TimePressure

**TimePressure** is an open-source autonomous agent runtime whose survival pressure is measured by time instead of capital.

The default rule is simple:

> **Earn at least US$0.01 during every one-hour cycle, or the agent dies.**

The project is intentionally conservative: revenue must be recorded as verified/legitimate revenue, secrets stay local, and Litecoin payouts use the operator's own Litecoin Core wallet.

## Status

This repository is an MVP runtime. The core pressure engine, CLI, local state, AI inference, Sign in with ChatGPT, safety policy, Litecoin RPC and payout ledger are implemented.

External prerequisites still apply: an eligible ChatGPT account for ChatGPT-plan OAuth usage, or an OpenAI API key; and a configured Litecoin Core wallet if payouts are desired.

## Install

Requirements: Node.js 20+.

```bash
git clone https://github.com/carlos210609/timepressure.git
cd timepressure
npm install
npm run build
npm link
```

## Quick start

Without AI:

```bash
timepressure doctor
timepressure status
timepressure revenue add 0.01 --source test --reference test-001
```

With an OpenAI API key:

```cp .env.example .env
# edit .env and set OPENAI_API_KEY
timepressure run```

With Sign in with ChatGPT:

```bash
timepressure login
timepressure login status
timepressure run
```

The OAuth flow opens the system browser and stores credentials under `~/.config/timepressure/` with owner-only permissions. OpenAI's current OSS flow uses PKCE and a loopback callback; eligible users can authorize ChatGPT-plan usage without supplying an API key. citeturn0search7turn0search5

## Pressure model

Default environment:

```env
TIMEPRESSURE_TARGET_CENTS=1
TIMEPRESSURE_CYCLE_MS=3600000
TIMEPRESSURE_TICK_MS=10000
```

The cycle is reset when recorded revenue reaches the target. Missing the deadline changes the agent to `dead`.

## Litecoin

TimePressure never stores a wallet seed or private key.

Configure Litecoin Core RPC:

```env
LTC_RPC_URL=http://127.0.0.1:9332/
LTC_RPC_USER=
LTC_RPC_PASSWORD=
LTC_PAYOUT_ADDRESS=
LTC_MIN_PAYOUT=0.001
LTC_AUTO_PAYOUT=false
LTC_USD_RATE=
```

Commands:

```bash
timepressure wallet balance
timepressure wallet address timepressure
timepressure wallet quote 1 80
timepressure wallet payout 0.001
timepressure wallet payout-earned 80
```

`wallet payout-earned` converts unpaid recorded revenue using the supplied LTC/USD rate, checks the minimum, sends the payout through Litecoin Core, and records the transaction ID and paid revenue references. It does not fetch a market price.

Automatic payout is disabled by default. If enabled, `LTC_USD_RATE` is required; after a revenue event is recorded, the runtime settles all currently unpaid revenue to `LTC_PAYOUT_ADDRESS` and records the TXID. The operator remains responsible for the configured exchange rate and wallet.

## Security model

- No private keys or wallet seeds in environment variables.
- Local OAuth credentials are stored outside the repository.
- Shell commands pass through a denylist safety policy.
- Relative file reads reject traversal and `.env` paths.
- Network access can be disabled with `TIMEPRESSURE_ALLOW_NETWORK=false`.
- Revenue references must be unique.
- Payouts track paid revenue references to prevent duplicate settlement.

This is an experimental autonomous-agent runtime. Review permissions and generated actions before running it unattended.

## Development

```bash
npm run typecheck
npm test
npm run build
```

## License

MIT.
