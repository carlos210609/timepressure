# Contributing to TimePressure

Thanks for helping improve TimePressure.

## Before you start

Please read the README and keep contributions aligned with the project's safety model. TimePressure may automate browser interactions, but contributions must not add spam, credential theft, CAPTCHA bypass, platform-limit evasion, impersonation, unauthorized access, or autonomous financial transactions.

## Development

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall timepressure timepressure.py
```

Keep changes focused and avoid introducing unnecessary dependencies.

## Pull requests

A good PR should:

- explain the problem being solved
- describe the implementation
- include tests when behavior changes
- update documentation when commands/configuration change
- avoid unrelated refactors
- call out security or permission implications

## Issues

For bugs, include your Python version, operating system, command, error output, and reproduction steps.

For feature requests, explain the user problem first and the proposed solution second.

## Strategy and revenue data

Do not add fabricated earnings, fake testimonials, fake payment records, or claims that a strategy is guaranteed to make money. Revenue examples must be clearly labeled as examples or verified records.

## Security

Do not publicly disclose credentials, API keys, wallet seeds, private keys, cookies, session tokens, or other secrets in issues or pull requests. For a suspected security vulnerability, avoid publishing exploit details until the maintainer has had an opportunity to review them.
