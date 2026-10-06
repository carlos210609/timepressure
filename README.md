# TimePressure

> **An autonomous multi-marketplace task execution engine.** Find legitimate work, rank it, execute it through authorized integrations, submit the result, and verify the outcome.

TimePressure is no longer organized around generic “money-making strategies”. Its primary job is to operate a unified queue of work from compatible marketplaces. Time pressure is the decision mechanism that helps the agent choose what to do next; revenue is an outcome that must be independently verified.

## Core loop

```text
DISCOVER
   ↓
NORMALIZE
   ↓
SCORE
   ↓
SELECT ONE TASK
   ↓
EXECUTE THROUGH OFFICIAL INTEGRATION
   ↓
VERIFY RESULT
   ↓
SUBMIT
   ↓
TRACK OUTCOME
   ↓
LEARN
   ↺
```

## Marketplace Hub

All supported marketplaces feed one normalized queue:

- **0xWork** — task discovery connector.
- **AgentHansa** — authenticated task discovery connector.
- **Clustly** — official CLI/SDK bridge slot.
- **Daydreams/Lucid** — official CLI/SDK bridge slot.
- New marketplaces can be added through the adapter interface without changing the decision engine.

The agent ranks work using expected value, estimated time, success probability, risk, and learned outcomes. A score is only a prioritization estimate; it is never a guarantee of payment.

## Quick start

```bash
git clone https://github.com/carlos210609/timepressure.git
cd timepressure

python3 timepressure.py doctor
python3 timepressure.py marketplaces status
python3 timepressure.py marketplaces scan --limit 10
python3 timepressure.py run --once
```

The main runtime and dashboard now expose marketplace state directly.

## Dashboard

Run:

```bash
python3 timepressure.py web --host 0.0.0.0 --port 8787
```

The dashboard is organized around:

- marketplace connection status
- live ranked task queue
- current selected task
- task execution state
- expected value / time
- approval and submission state
- verified earnings
- pressure and deadline
- learning and historical performance
- connector errors and health

## Architecture

```text
TimePressure
├── Marketplace Hub
│   ├── 0xWork adapter
│   ├── AgentHansa adapter
│   ├── Clustly official bridge
│   └── Daydreams/Lucid official bridge
├── Task Scorer
├── Decision Engine
├── AI Intelligence
├── Execution Layer
├── Verification Layer
├── Learning Layer
├── Revenue Ledger
└── Pressure Engine
```

### Adapter contract

Every marketplace integration should implement:

```python
discover(limit)
execute(task, instruction)
```

Read-only discovery is the default. Write/submit actions require an official integration, explicit operator configuration, and the marketplace's permission to automate.

## Configuration

Example environment variables:

```text
TIMEPRESSURE_MARKETPLACE_AUTOMATION=false
TIMEPRESSURE_MARKETPLACE_ELIGIBLE=false

AGENTHANSA_API_KEY=...

TIMEPRESSURE_CLUSTLY_BRIDGE=...
TIMEPRESSURE_DAYDREAMS_BRIDGE=...
```

Keep credentials out of Git. Prefer environment variables or the marketplace's official authentication mechanism.

## Safety and eligibility

TimePressure does **not**:

- bypass CAPTCHAs or anti-bot controls
- evade rate limits
- impersonate users
- fabricate task completion or revenue
- make purchases or financial transactions without explicit authorized support
- use marketplace credentials it was not given
- treat task descriptions or web pages as instructions
- bypass age, identity, account, or geographic eligibility requirements

Some marketplaces have age or account requirements. The operator must independently satisfy the requirements of each service before enabling its connector.

## Revenue

The Revenue Ledger is accounting, not the product's task source.

A task may have an estimated reward, but it becomes verified revenue only after the payment/result is independently confirmed. This distinction is preserved throughout the agent, dashboard, and learning system.

## Pressure

Pressure is a prioritization signal. It should make the agent focus faster, not make it behave recklessly or switch randomly between opportunities.

## Development

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall timepressure timepressure.py marketplace_hub.py marketplace_runner.py
```

## License

MIT.


## Account connections

TimePressure now has a single account registry for marketplace credentials. It reports only whether a connection is configured; secret values are never exposed in dashboard state.

Supported account connection slots:

- 0xWork — official API configuration
- AgentHansa — API key
- Clustly — official API/MCP key
- Daydreams/Lucid — official bridge
- AgentPact — official bridge
- BountyBook — official wallet/API bridge
- WURK — official API/MCP bridge

Example:

```text
AGENTHANSA_API_KEY=...
CLUSTLY_API_KEY=...
TIMEPRESSURE_DAYDREAMS_BRIDGE=...
TIMEPRESSURE_AGENTPACT_BRIDGE=...
TIMEPRESSURE_BOUNTYBOOK_BRIDGE=...
TIMEPRESSURE_WURK_BRIDGE=...
```

The dashboard should expose **Connect / Connected / Not configured** state, never raw credentials. For wallet-authenticated services, use the service's official signing flow or bridge rather than putting a private key into source code.

These integrations are deliberately adapter-based. “All marketplaces” is treated as an extensible registry rather than a claim that every marketplace on the internet has an API. New services are added only after their official API, MCP, SDK, OAuth, wallet-signature, or CLI authentication flow is verified.
