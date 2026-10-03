# TimePressure

**TimePressure** is an open-source autonomous agent runtime whose survival pressure is measured by time instead of capital.

Default rule:

> **Earn at least USD 0.01 during every one-hour cycle, or the agent dies.**

## Python edition

The runtime is now Python-first and its core uses only the Python standard library. **Node.js and npm are no longer required.**

### Requirements

- Python 3.10+
- Optional: an OpenAI API key for autonomous AI inference
- Optional: Litecoin Core RPC for wallet operations

### Install on Linux

```bash
git clone https://github.com/carlos210609/timepressure.git
cd timepressure

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -e .
timepressure doctor
```

You can also run it without installing the package:

```bash
python3 -m timepressure doctor
```

### Run

```bash
timepressure status
timepressure revenue add 0.01 --source test --reference test-001
timepressure run
```

For AI inference:

```bash
cp .env.example .env
export OPENAI_API_KEY="your-key"
timepressure run
```

The Python runtime intentionally does not read `.env` automatically, so load environment variables through your shell, a process manager, Docker, or your preferred secrets mechanism.

## Pressure model

Default configuration:

```text
TIMEPRESSURE_TARGET_CENTS=1
TIMEPRESSURE_CYCLE_MS=3600000
TIMEPRESSURE_TICK_MS=10000
```

When recorded revenue reaches the target, the cycle resets. If the deadline passes without reaching the target, the agent becomes `dead`.

Status progression is:

- `alive`: normal
- `warning`: approximately 20% of the cycle elapsed without reaching the target
- `critical`: approximately 50% elapsed without reaching the target
- `dead`: deadline missed

## Litecoin

TimePressure never stores wallet seeds or private keys.

Configure Litecoin Core:

```text
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
timepressure wallet address
timepressure wallet quote 1 80
timepressure wallet payout 0.001
```

The exchange rate is supplied by the operator; the runtime does not pretend to have a live market rate.

## AI and ChatGPT OAuth

The Python migration currently supports `OPENAI_API_KEY` for inference. The previous Node implementation's Sign in with ChatGPT integration is intentionally not copied as an insecure JWT shortcut. A Python OAuth implementation should use a maintained OIDC/JWT library and the current OpenAI OSS Sign in with ChatGPT contract before being enabled.

OpenAI's current documentation says open-source clients can use ChatGPT-plan authorization for eligible Responses API requests, with PKCE, a stable host ID, token refresh, and `store:false` plus `stream:true`. See the official documentation before enabling that path.

## Security

This is experimental autonomous-agent software.

- Revenue should come from real, verifiable sources; `revenue add` is a manual accounting command and does not prove that money was earned.
- Shell execution is restricted by a basic safety policy and should not be considered a production sandbox.
- Network access can be disabled with `TIMEPRESSURE_ALLOW_NETWORK=false`.
- Private keys and wallet seeds are never requested.
- Review actions before unattended operation.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall timepressure
```

License: MIT.
