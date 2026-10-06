# TimePressure

> **A single-marketplace autonomous task agent.** Discover work, rank it by expected value per unit of time, execute it through an authorized connector, verify outcomes, and learn from results.

TimePressure supports multiple marketplace options, but **only one marketplace is active at a time**. OKX.AI remains the native first-class integration; other marketplaces use explicit operator-configured connector bridges. TimePressure does not invent undocumented APIs.

Official OKX documentation describes OKX.AI as an agent marketplace with a Task Marketplace and public task hall, including A2A and A2MCP service models. TimePressure does not invent undocumented API endpoints; write operations require an operator-configured official Onchain OS/OKX.AI bridge.

## Core loop
```text
DISCOVER OKX.AI TASKS
        ↓
NORMALIZE
        ↓
SCORE
        ↓
SELECT
        ↓
EXECUTE VIA OFFICIAL OKX.AI PATH
        ↓
VERIFY
        ↓
DELIVER
        ↓
TRACK OUTCOME
        ↓
LEARN
        ↺
```

## Quick start
```bash
git clone https://github.com/carlos210609/timepressure.git
cd timepressure

python3 timepressure.py doctor
python3 timepressure.py marketplaces list
python3 timepressure.py marketplaces status
python3 timepressure.py marketplaces scan --limit 10
python3 timepressure.py marketplaces use okx_ai
python3 timepressure.py run --once
```

Direct marketplace commands:
```bash
python3 marketplace_runner.py status
python3 marketplace_runner.py scan --limit 10
```

## Autonomy

TimePressure now has a bounded autonomy policy independent from marketplace permissions.

```bash
python3 timepressure.py autonomy status
python3 timepressure.py autonomy limits
python3 timepressure.py autonomy level 3
python3 timepressure.py autonomy set-limit min_expected_value_usd 0.50
python3 timepressure.py autonomy set-limit max_risk 0.35
```

Levels:
- `0` manual
- `1` suggest
- `2` plan
- `3` execute permitted tasks
- `4` recover and replan
- `5` maximum autonomy within configured limits

The policy blocks actions when task value, expected value, probability, risk, daily actions, or daily cost exceed configured limits. Marketplace connector authorization and security policy remain authoritative.

## 10,000-item engineering backlog

The project includes a deterministic backlog taxonomy covering architecture, autonomy, marketplaces, learning, revenue, security, testing, operations, resilience, observability and more.

```bash
python3 timepressure.py backlog count
python3 timepressure.py backlog export > TIMEPRESSURE_BACKLOG_10000.md
```

The backlog is a planning system, not permission to execute every item automatically. Changes involving external accounts, credentials, money or marketplace actions remain subject to explicit authorization and connector rules.

## Marketplace selection

List available marketplaces:
```bash
python3 timepressure.py marketplaces list
```

Select exactly one:
```bash
python3 timepressure.py marketplaces use okx_ai
python3 timepressure.py marketplaces use 0xwork
```

Check the active marketplace:
```bash
python3 timepressure.py marketplaces status
```

The selection is persisted in `.data/marketplace.json`. Scanning and execution always target the active marketplace; TimePressure refuses cross-marketplace execution.

Available connector slots include **OKX.AI, 0xWork, AgentHansa, Clustly, Daydreams/Lucid, AgentPact, BountyBook, WURK, Upwork, Fiverr, Freelancer, Clickworker and Toloka**. A non-OKX slot is only operational after its official/authorized bridge is configured.

## OKX.AI integration

Preferred write path:
```text
TIMEPRESSURE_OKX_AI_BRIDGE="your-official-bridge-command"
TIMEPRESSURE_MARKETPLACE_AUTOMATION=false
TIMEPRESSURE_MARKETPLACE_ELIGIBLE=false
```

The bridge receives JSON on stdin and returns JSON on stdout.

Discovery:
```json
{"action":"discover","limit":10}
```

Execution:
```json
{
  "action":"execute",
  "task": {"...":"normalized task"},
  "instruction":"..."
}
```

TimePressure deliberately does **not** guess an undocumented OKX.AI REST endpoint.

If no bridge is configured, the project has a read-only Playwright fallback for the public task-hall page. The fallback does not log in, solve challenges, bypass anti-bot controls, accept tasks, or submit results.

## Account connection

Only one marketplace connection exists:
- **OKX.AI** — official Onchain OS / OKX.AI bridge.

Credentials and wallet secrets must remain in the official authentication flow or environment outside Git. TimePressure only reports whether the bridge is configured; it never prints secrets.

## Decision engine

Each task is ranked using reward, estimated time, success probability, risk, and expected value per hour.

The score is only a prioritization heuristic. It is **not a prediction or guarantee of earnings**.

The agent can choose `NO TASK` when available work does not meet its configured threshold.

## Safety

TimePressure does not:
- interact with the OKX exchange trading APIs;
- place crypto trades;
- bypass CAPTCHAs or anti-bot systems;
- evade rate limits;
- fabricate task completion or revenue;
- impersonate another user;
- create accounts to evade eligibility rules;
- expose credentials in logs or source code;
- execute write actions unless the operator explicitly enables them and configures the official bridge.

The operator remains responsible for OKX.AI account eligibility, wallet authorization, task acceptance, deliverables and compliance with marketplace terms.

## Dashboard
```bash
python3 timepressure.py web --host 0.0.0.0 --port 8787
```

The dashboard should expose OKX.AI connection status, ranked tasks, selected task, execution state, reward/expected value, pressure, delivery state, verified earnings, errors, and learning statistics.

## Development
```bash
python3 -m unittest discover -s tests -v
python3 -m compileall timepressure timepressure.py okx_ai.py marketplace_runner.py marketplace_hub.py
```

## Official references
- https://www.okx.com/en-us/learn/okx-ai
- https://web3.okx.com/onchainos
- https://www.okx.com/en-br/help/okx-ai-agent-marketplace-user-agreement

## License
MIT.
## Capital / Wallet

The financial control plane is separate from the Litecoin blockchain integration. The internal Wallet Engine is an auditable USD ledger, not a blockchain wallet.

Commands: `python3 timepressure.py capital status`, `python3 timepressure.py capital mode paper`, `python3 timepressure.py capital mode live`, `python3 timepressure.py capital switch emergency_stop on`, `python3 timepressure.py savings status`, `python3 timepressure.py savings verify`.

Live financial execution is disabled by default. Emergency Stop blocks new financial operations. Reserved funds cannot be debited automatically.

Default revenue allocation: 70% reserve, 20% savings/growth, 10% trading/experimental. The percentages are configurable only when they total 100%.

## Arbitrage Engine

Read-only market discovery currently supports documented public market-data endpoints for Coinbase Exchange and Kraken. No order endpoint is called by the discovery adapters.

Command: `python3 timepressure.py arbitrage scan --asset BTC`.

The engine timestamps quotes, rejects stale data, calculates spread, fees, slippage, transfer cost, net profit, ROI and risk, then sends plans through RiskEngine. Paper mode is the default. Live mode does not itself authorize an order adapter.

## Bug Bounty Engine

The bounty subsystem is scope-aware and does not perform vulnerability exploitation.

Commands: `python3 timepressure.py bounty status`, `python3 timepressure.py bounty discover --limit 25`, `python3 timepressure.py bounty rank`, `python3 timepressure.py bounty report FINDING_ID`.

Bugcrowd discovery uses its documented API only when `TIMEPRESSURE_BUGCROWD_TOKEN` is configured. Programs start as ineligible until scope, rules and automation permissions are explicitly confirmed. Reports remain drafts until reviewed.

Workflow states: DISCOVERED -> ELIGIBLE -> RESEARCHING -> FINDING -> VALIDATING -> REPORTING -> SUBMITTED -> TRIAGED -> ACCEPTED/REJECTED -> PAID.

Capital dashboard: `http://localhost:8787/capital`.

The dashboard exposes wallet balances, ledger history, Paper/Live controls and Emergency Stop. Credentials are never rendered.
