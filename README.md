# TimePressure

**TimePressure** is an open-source autonomous agent runtime whose survival pressure is measured by time instead of capital.

Default rule:

> **Earn at least USD 0.01 during every one-hour cycle, or the agent dies.**

## Zero-setup launch

You do **not** need Node.js, npm, a virtual environment, or a manual dependency-install step.

After cloning:

```bash
git clone https://github.com/carlos210609/timepressure.git
cd timepressure
python3 timepressure.py
```

On the first launch, `timepressure.py` automatically:

- installs the required Python packages;
- installs Playwright's Chromium browser;
- installs `python3-tk` automatically on Debian/Ubuntu-based Linux when possible;
- starts the Tkinter desktop interface.

On later launches, it reuses the installed dependencies and starts normally.

Git itself intentionally does not execute repository code during `git clone`; the first `python3 timepressure.py` launch is the safe bootstrap step.

## Requirements

- Python 3.10+
- Internet connection for the first bootstrap
- Optional: Litecoin Core RPC for wallet operations

## AI and ChatGPT

The desktop interface uses Tkinter and OpenAI/ChatGPT as the intelligence layer. Preferred authentication is Sign in with ChatGPT OAuth; an OpenAI API key remains an optional fallback.

The OAuth implementation uses PKCE, state/nonce validation, token refresh and ID-token verification. Actual OAuth availability depends on the user's OpenAI account and current service eligibility.

## Pressure model

Default configuration:

```text
TIMEPRESSURE_TARGET_CENTS=1
TIMEPRESSURE_CYCLE_MS=3600000
TIMEPRESSURE_TICK_MS=10000
```

When recorded revenue reaches the target, the cycle resets. If the deadline passes without reaching the target, the agent becomes `dead`.

Status progression:

- `alive`: normal
- `warning`: approximately 20% of the cycle elapsed without reaching the target
- `critical`: approximately 50% elapsed without reaching the target
- `dead`: deadline missed

## Browser access

TimePressure can use a real Chromium browser through Playwright to research opportunities and interact with explicitly allowed websites.

Browser navigation is HTTPS-only and requires:

```text
TIMEPRESSURE_BROWSER_ENABLED=true
TIMEPRESSURE_BROWSER_HEADLESS=true
TIMEPRESSURE_BROWSER_ALLOWED_DOMAINS=example.com,another-site.com
```

The browser deliberately does **not** provide automatic purchase/payment/financial-submit tools. The agent is also instructed not to spam, bypass CAPTCHAs, evade platform limits or impersonate people.

## Litecoin

TimePressure never stores wallet seeds or private keys.

Configure Litecoin Core with:

```text
LTC_RPC_URL=http://127.0.0.1:9332/
LTC_RPC_USER=
LTC_RPC_PASSWORD=
LTC_PAYOUT_ADDRESS=
LTC_MIN_PAYOUT=0.001
LTC_AUTO_PAYOUT=false
LTC_USD_RATE=
```

The exchange rate is supplied by the operator; the runtime does not pretend to have a live market rate.

## Security

This is experimental autonomous-agent software.

- Revenue should come from real, verifiable sources; `revenue add` is manual accounting and does not prove money was earned.
- Shell execution is disabled by default.
- Network access can be disabled with `TIMEPRESSURE_ALLOW_NETWORK=false`.
- Browser access uses an explicit HTTPS domain allowlist.
- Private keys and wallet seeds are never requested.
- Financial and irreversible actions require human review.

## Tests

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall timepressure
```

License: MIT.
