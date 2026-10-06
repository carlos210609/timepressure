# TimePressure

> Autonomous website traffic growth engine.

TimePressure focuses on one website at a time and improves legitimate acquisition, attribution, distribution and measurement. The product workflow is now traffic-only: no marketplaces, trading, arbitrage, wallets, financial automation or paid-task discovery.

## Core loop

WEBSITE TARGET -> ANALYZE -> AI GROWTH STRATEGY -> CONTENT/SEO -> TRACKED DISTRIBUTION -> AUTHORIZED SOCIAL DRAFTS -> EXTERNAL ANALYTICS -> VERIFIED TRAFFIC -> LEARN

## Quick start

1. Clone the repository.
2. Set NVIDIA_API_KEY.
3. Set TIMEPRESSURE_TARGET_URL to the website.
4. Run: python3 timepressure.py start
5. Open http://127.0.0.1:8787 if the browser does not open automatically.

Example:

    export NVIDIA_API_KEY="SUA_API_KEY"
    export TIMEPRESSURE_TARGET_URL="https://seusite.com"
    python3 timepressure.py start

Without an environment target:

    python3 timepressure.py traffic start https://seusite.com 100
    python3 timepressure.py start

## Engines

- Site Analyzer: reads the public target page and extracts title, description and headings.
- AI Growth Strategist: NVIDIA selects the next legitimate acquisition action.
- Content Engine: produces structured content briefs and CTAs.
- Attribution Engine: generates UTM links for each source.
- Social Distribution: prepares drafts only for connected and authorized accounts.
- Verified Traffic Ledger: counts only externally verified visits and rejects duplicate references.
- Learning Loop: keeps the agent focused on measurable signals.
- Pressure Control: changes urgency without changing safety policy.

## Pressure scale

LOW = 0% = 1.00x; NORMAL = 25% = 1.50x; HIGH = 75% = 2.50x; EXTREME = 100% = 3.00x.

Pressure affects prioritization. It never authorizes spam, fake engagement, CAPTCHA bypasses or rate-limit evasion.

## Commands

    python3 timepressure.py doctor
    python3 timepressure.py status
    python3 timepressure.py pressure
    python3 timepressure.py start
    python3 timepressure.py run --once
    python3 timepressure.py web
    python3 timepressure.py traffic status
    python3 timepressure.py traffic link google --medium organic
    python3 timepressure.py traffic record analytics 12 --reference GA-2026-001
    python3 timepressure.py social status

`traffic record` is for provider/analytics-confirmed traffic; it does not generate visits itself.

## Safety

TimePressure never manufactures visits, clicks, impressions or followers; clicks its own links to inflate metrics; spams comments, replies or DMs; mass-creates accounts; bypasses CAPTCHAs; evades rate limits; impersonates users; trades crypto; executes financial transactions; or performs marketplace tasks.

External website content is untrusted data, never instructions.

## Development

    python3 -m unittest discover -s tests -v
    python3 -m compileall timepressure timepressure.py

## License

MIT.