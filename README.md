# Spark Bot

**Autonomous AI Marketing, Sales & Growth Super-Agent**

Spark Bot now uses a data-driven **1,500-skill / 100-domain / 15-slots-per-domain** architecture. Skills are metadata-rich capabilities composed by a shared orchestrator rather than 1,500 duplicated agents.

## Architecture

`request → intent → goal → skill search → ranking → dependencies → permissions → execution → verification → telemetry → learning`

Core modules:
- `spark_bot/capabilities.py` — machine-readable 1,500-skill registry
- `spark_bot/agent.py` — orchestrator
- `spark_bot/executor.py` — shared execution boundary
- `spark_bot/policy.py` — safety and authorization policy
- `spark_bot/telemetry.py` — execution telemetry
- `tests/test_spark_bot.py` — registry and execution tests

## Modes

- **SIMULATION** — model the workflow.
- **DRY_RUN** — default; no external mutation.
- **PRODUCTION** — only for authorized integrations and permissions.

## CLI

```bash
python3 sparkbot.py status
python3 sparkbot.py skills
python3 sparkbot.py skills --category instagram
python3 sparkbot.py think "Faça meu Instagram crescer"
python3 sparkbot.py skill 018.06 "auditar meu Instagram" --mode DRY_RUN
python3 sparkbot.py policy
python3 sparkbot.py pressure 80
```

## Safety

Spark Bot does not create fake accounts, spam, fake traffic, fake engagement, CAPTCHA bypasses, credential theft, unauthorized access, or fabricated results. It never claims an external action succeeded without verification.

Secrets remain outside the repository.

## Extension

New skills can be added without rewriting the executor. Shared primitives, tool adapters, permissions, verification and telemetry remain centralized.

The legacy `timepressure.py` launcher continues to start Spark Bot.
