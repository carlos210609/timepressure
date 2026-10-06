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