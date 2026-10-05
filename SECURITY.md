# Security Policy

## Supported versions

The latest version on the `main` branch is the primary development target.

## Reporting a vulnerability

Please do not publish credentials, tokens, wallet secrets, session cookies, or a working exploit in a public issue.

If GitHub's private vulnerability reporting is enabled for this repository, use it. Otherwise, contact the maintainer privately through the contact method available on the GitHub profile.

Include:

- affected version/commit
- impact
- reproduction steps
- relevant logs with secrets removed
- a suggested mitigation if you have one

## Security principles

TimePressure should:

- keep credentials in environment/configuration mechanisms rather than source control
- avoid storing wallet seeds or private keys
- require explicit browser domain allowlists
- keep irreversible financial actions under human review
- avoid CAPTCHA bypass, spam, impersonation, and platform-limit evasion

Never commit API keys, cookies, private keys, wallet seeds, or personal access tokens.
