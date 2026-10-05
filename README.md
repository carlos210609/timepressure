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
timepressure revenue add 0.10 --source verified-source
timepressure browser open https://example.com
timepressure wallet balance
~~~

No command starts a desktop interface.

## Survival rule

Default target: USD 0.10 per hour.

If the target is reached, the cycle resets. If the deadline passes first, the agent becomes dead and must be reset explicitly.

~~~text
TIMEPRESSURE_TARGET_CENTS=10
TIMEPRESSURE_CYCLE_MS=3600000
TIMEPRESSURE_TICK_MS=10000
~~~

## ChatGPT

Preferred authentication is ChatGPT OAuth. An OpenAI API key is an optional fallback. OAuth uses PKCE, state/nonce validation, token refresh and ID-token verification.

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

Revenue entries are accounting records and do not prove earnings. Shell execution is disabled by default. Network access can be disabled. Financial or irreversible actions require human review.

## Tests

~~~bash
python3 -m unittest discover -s tests -v
python3 -m compileall timepressure timepressure.py
~~~

License: MIT.
