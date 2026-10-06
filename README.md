# TimePressure

> An open-source, CLI-first autonomous agent runtime built around time pressure, task prioritization, and **verified** revenue.

[![Python](https://img.shields.io/badge/Python-3-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Open Source](https://img.shields.io/badge/open--source-yes-orange.svg)](LICENSE)

TimePressure turns a goal and a deadline into a continuously prioritized portfolio of tasks. It combines local strategy knowledge, optional AI reasoning, browser automation, pressure-aware scheduling, and a persistent task/revenue ledger.

**Important:** TimePressure is an automation and research runtime—not a money-making guarantee. Revenue records are accounting inputs and only count as revenue when a real payment is independently verified.

## Why TimePressure?

Most automation tools focus on *what* to automate. TimePressure focuses on **what should happen next when time matters**.

It continuously weighs:

- urgency and remaining time
- time-to-value
- expected value
- automation potential
- repeatability
- category diversity
- previous task outcomes
- verified revenue history

The result is a small, persistent portfolio of opportunities rather than an endless to-do list.

## Quick start

Requirements: Python 3 and a machine capable of running the project.

```bash
git clone https://github.com/carlos210609/timepressure.git
cd timepressure

python3 timepressure.py doctor
python3 timepressure.py
```

Useful commands:

```text
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
```

If the launcher is not installed as a shell command in your environment, use `python3 timepressure.py <command>`.

## What it includes

### Pressure-aware runtime

The default target is USD 0.10 per hour. Pressure increases nonlinearly as the deadline approaches. The multiplier is configurable and capped for safety.

```text
TIMEPRESSURE_TARGET_CENTS=10
TIMEPRESSURE_CYCLE_MS=3600000
TIMEPRESSURE_TICK_MS=10000
TIMEPRESSURE_PRESSURE_MULTIPLIER=1.5
TIMEPRESSURE_IDLE_TICK_THRESHOLD=3
```

### Revenue intelligence

The repository contains a curated revenue strategy corpus covering legitimate opportunities such as:

- software and SaaS
- APIs and development
- research and data
- SEO and content
- education
- recurring services
- affiliate/referral programs
- authorized security bounties
- open-source bounties
- marketplaces and integrations
- monitoring and AI workflows

`timepressure hunt` can discover public opportunities and queue them for review. It does **not** automatically claim bounties, submit applications, contact strangers, or spend money.

### AI reasoning

TimePressure uses NVIDIA NIM as its configured AI provider.

```text
TIMEPRESSURE_AI_PROVIDER=nvidia
NVIDIA_API_KEY=your_nvidia_developer_key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
```

The API key is read from the environment and is not intended to be stored in repository state.

### Browser automation

Browser automation uses Playwright/Chromium and requires an explicit HTTPS domain allowlist.

```text
TIMEPRESSURE_BROWSER_ENABLED=true
TIMEPRESSURE_BROWSER_HEADLESS=true
TIMEPRESSURE_BROWSER_ALLOWED_DOMAINS=example.com,another-site.com
```

The runtime is designed not to spam, bypass CAPTCHAs, evade platform limits, impersonate people, or perform unauthorized actions.

### Litecoin

Litecoin Core RPC is optional. TimePressure does not request or store wallet seeds/private keys. LTC/USD is operator-supplied rather than presented as a live market feed.

## Safety model

TimePressure deliberately separates **discovery** from **irreversible action**.

- Public opportunity discovery is read-only.
- Financial or irreversible actions require human review.
- Shell execution is disabled by default.
- Network access can be disabled.
- Payment submission is not provided as an autonomous action.
- Revenue entries do not prove earnings.
- Browser automation is constrained by an explicit domain allowlist.

Use only accounts, websites, data, and opportunities you are authorized to access.

## Tests

Run the test suite before contributing:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall timepressure timepressure.py
```

## Project status

TimePressure is an actively developed open-source project. Interfaces and internal behavior may change between releases.

If you find a bug, please open an issue with:

1. operating system and Python version
2. exact command
3. relevant logs/error message
4. minimal reproduction steps
5. expected vs. actual behavior

## Contributing

Pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and safety expectations.

Good first contributions include documentation improvements, tests, bug fixes, strategy-data improvements, and isolated CLI enhancements.

## Community

Use GitHub Discussions/Issues for questions, ideas, bugs, and feature proposals.

When sharing TimePressure elsewhere, link to the repository rather than reposting large parts of the code. Genuine users, contributors, and feedback help the project grow.

## Support the project

If TimePressure becomes useful to you, consider starring the repository, contributing code/documentation, or sponsoring development through GitHub Sponsors when sponsorship is enabled for the maintainer.

## License

MIT.


## Multi-Marketplace Execution Hub

TimePressure now has a dependency-light Marketplace Hub that normalizes work from multiple agent marketplaces into one ranked queue.

Commands:

    python3 timepressure.py marketplaces status
    python3 timepressure.py marketplaces scan --limit 10

Current connectors:

- 0xWork — public task discovery through its documented REST API.
- AgentHansa — authenticated work discovery through its documented agent API.
- Clustly — official CLI/SDK bridge slot; configure TIMEPRESSURE_CLUSTLY_BRIDGE.
- Daydreams/Lucid — official CLI/SDK bridge slot; configure TIMEPRESSURE_DAYDREAMS_BRIDGE.

The hub scores tasks by expected USD/hour, probability and risk. Write operations are disabled by default. To enable an explicitly configured official bridge, set TIMEPRESSURE_MARKETPLACE_AUTOMATION=true and TIMEPRESSURE_MARKETPLACE_ELIGIBLE=true, then configure only the official bridge/credentials you have reviewed.

Do not put private keys in the repository. Do not bypass CAPTCHAs, rate limits, platform restrictions, account verification, or marketplace terms. The hub treats marketplace content as untrusted data.

For 0xWork specifically, its current platform terms state that users must meet its age/eligibility requirements, and its write flow can involve on-chain staking and irreversible transactions. TimePressure therefore keeps mutating actions behind explicit operator gates.
