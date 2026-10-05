# TimePressure

Open-source autonomous agent runtime driven by time pressure and verified revenue.

## CLI-first

TimePressure has no Tkinter, desktop GUI, Node.js, npm, or virtual environment.

~~~bash
git clone https://github.com/carlos210609/timepressure.git
cd timepressure
python3 timepressure.py
~~~

First launch installs the required Python packages and Playwright Chromium. Git does not execute repository code during clone; the Python launcher is the explicit bootstrap step.

## Quick start

~~~bash
python3 timepressure.py
python3 timepressure.py auth login
python3 timepressure.py doctor
python3 timepressure.py run
~~~

Useful commands:

~~~text
timepressure auth login
timepressure auth status
timepressure auth logout
timepressure doctor
timepressure status
timepressure status --watch
timepressure run
timepressure run --once
timepressure reset
timepressure hunt
timepressure tasks
timepressure revenue add 0.10 --source verified-source --strategy website_audit
timepressure browser open https://example.com
timepressure wallet balance
~~~

No command starts a desktop interface.

## Revenue intelligence

TimePressure includes a built-in revenue strategy playbook covering product, SaaS, APIs, development, research, SEO, data, content, education, recurring services, affiliate/referral programs, authorized security bounties, open-source bounties, marketplaces, integrations, monitoring and AI workflows.

The multitask engine ranks opportunities using pressure, time-to-value, expected value, automation potential, repeatability and category diversity. It maintains a persistent portfolio of up to six active opportunities in `.data/tasks.json` and chooses the highest-priority safe task on each agent tick. `timepressure hunt` also discovers public bounty opportunities and queues them without submitting work or spending money. `timepressure tasks` exposes the active portfolio and learned strategy statistics in `.data/strategy_stats.json`.

This is a strategy database, not a guarantee of income. A strategy becomes revenue only after a legitimate payment is actually verified. The learning loop should be fed with verified revenue using `--strategy`; failed/completed task outcomes are also retained so future prioritization can improve.

## Survival rule

Default target: USD 0.10 per hour.

If the target is reached, the cycle resets. If the deadline passes first, the agent becomes dead and must be reset explicitly.

~~~text
TIMEPRESSURE_TARGET_CENTS=10
TIMEPRESSURE_CYCLE_MS=3600000
TIMEPRESSURE_TICK_MS=10000
~~~

## AI providers

TimePressure supports ChatGPT/OpenAI and NVIDIA NIM hosted APIs. NVIDIA hosted endpoints are OpenAI-compatible. Set `TIMEPRESSURE_AI_PROVIDER=nvidia` and configure `NVIDIA_API_KEY`. The default NVIDIA model is `nvidia/nemotron-3-super-120b-a12b`.

```text
TIMEPRESSURE_AI_PROVIDER=nvidia
NVIDIA_API_KEY=your_nvidia_developer_key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
```

NVIDIA states that its Developer Program provides free access to NIM API endpoints for prototyping, research and application development, subject to current limits and terms. The key is read only from the environment and is not stored in TimePressure state or exposed by the dashboard.

Use `TIMEPRESSURE_AI_PROVIDER=auto` to keep provider selection flexible, or force `nvidia` / `openai`.

ChatGPT OAuth remains supported. OAuth uses PKCE, state/nonce validation, token refresh and ID-token verification.

## Browser

Browser automation uses Playwright/Chromium and requires an explicit HTTPS domain allowlist:

~~~text
TIMEPRESSURE_BROWSER_ENABLED=true
TIMEPRESSURE_BROWSER_HEADLESS=true
TIMEPRESSURE_BROWSER_ALLOWED_DOMAINS=example.com,another-site.com
~~~

The agent does not provide purchase/payment submission tools and is instructed not to spam, bypass CAPTCHAs, evade platform limits or impersonate people.

## Litecoin

Litecoin Core RPC is optional. The runtime never requests or stores wallet seeds/private keys. The LTC/USD rate is operator-supplied, not claimed as a live market feed.

## Security

Revenue entries are accounting records and do not prove earnings. Opportunity discovery is intentionally read-only: it can find public leads, but it does not automatically claim bounties, submit applications, contact strangers, or move money. Shell execution is disabled by default. Network access can be disabled. Financial or irreversible actions require human review.

## Tests

~~~bash
python3 -m unittest discover -s tests -v
python3 -m compileall timepressure timepressure.py
~~~

License: MIT.
