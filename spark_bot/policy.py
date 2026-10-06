from __future__ import annotations

BLOCKED_PATTERNS = (
    "fake traffic", "bot traffic", "click fraud", "click manipulation",
    "fake account", "mass account", "spam", "credential theft",
    "captcha bypass", "rate-limit bypass", "impersonation",
)

def validate_objective(text: str):
    lowered = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lowered:
            return False, f"Blocked unsafe objective: {pattern}"
    return True, "allowed"

def account_policy():
    return {
        "automatic_temp_email_accounts": False,
        "reason": "Disposable/fake accounts can violate platform rules and enable abuse.",
        "supported": [
            "local identity generation for drafts/tests",
            "OAuth/API connections explicitly authorized by the user",
            "official signup flows when the user is present and the service permits automation",
        ],
    }

def marketing_policy():
    return {
        "allowed": [
            "SEO and content strategy", "authorized social publishing",
            "opt-in email campaigns", "partnership outreach",
            "analytics and attribution", "legitimate directories",
            "conversion optimization",
        ],
        "disallowed": [
            "fake visits/clicks/impressions", "spam", "fake accounts",
            "deceptive engagement", "CAPTCHA bypass", "credential theft",
            "unauthorized posting",
        ],
    }
