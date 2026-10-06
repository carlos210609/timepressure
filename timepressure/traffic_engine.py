"""Focused website traffic growth engine.

The engine only works on legitimate website-growth activities. It never
manufactures visits, clicks, impressions, followers, or engagement.
"""
from __future__ import annotations

import json
import re
import time
from html import unescape
from urllib.parse import urlparse

from .security import assert_https_public_url
from .traffic import campaign_url
from .social import queue_post


ALLOWED_ACTIONS = (
    "analyze_site",
    "create_utm_link",
    "create_content_brief",
    "queue_social_draft",
    "measure_verified_traffic",
)


def validate_target(url: str) -> str:
    parsed = assert_https_public_url(url.strip())
    return parsed.geturl()


def extract_site_facts(html: str) -> dict:
    title = re.search(r"<title[^>]*>(.*?)</title>", html or "", re.I | re.S)
    description = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        html or "",
        re.I | re.S,
    )
    headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html or "", re.I | re.S)
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html or "", flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return {
        "title": re.sub(r"\s+", " ", unescape(title.group(1))).strip() if title else "",
        "description": re.sub(r"\s+", " ", unescape(description.group(1))).strip() if description else "",
        "headings": [re.sub(r"\s+", " ", unescape(x)).strip() for x in headings[:20]],
        "textPreview": text[:1600],
        "htmlBytes": len((html or "").encode("utf-8")),
    }


def build_growth_plan(target_url: str, facts: dict, pressure: float, social_accounts: int = 0) -> list[dict]:
    domain = urlparse(target_url).netloc
    plan = [
        {
            "action": "analyze_site",
            "priority": 1,
            "reason": "Keep the target page and its search intent as the single source of truth.",
            "expectedSignal": "A clearer title, description, headings and conversion path.",
        },
        {
            "action": "create_content_brief",
            "priority": 2,
            "reason": "Create useful search-oriented content around the site's actual offer.",
            "expectedSignal": "A publishable brief with one intent, one audience and one CTA.",
        },
        {
            "action": "create_utm_link",
            "priority": 3,
            "reason": "Every distribution channel needs attribution.",
            "expectedSignal": "Visits can be attributed by source and campaign.",
        },
    ]
    if social_accounts:
        plan.append({
            "action": "queue_social_draft",
            "priority": 4,
            "reason": "Prepare distribution for connected, operator-authorized social accounts.",
            "expectedSignal": "A useful non-spam post is ready for human/provider approval.",
        })
    plan.append({
        "action": "measure_verified_traffic",
        "priority": 5,
        "reason": "Only provider/analytics-confirmed traffic counts as progress.",
        "expectedSignal": "Verified visits, sources and conversion signals.",
    })
    return sorted(plan, key=lambda x: x["priority"])


def make_content_brief(target_url: str, facts: dict) -> dict:
    title = facts.get("title") or urlparse(target_url).netloc
    description = facts.get("description") or "the website's core offer"
    return {
        "title": f"Content brief for {title}",
        "searchIntent": "informational-to-commercial",
        "audience": "people actively looking for the site's core offer",
        "angle": description[:240],
        "outline": [
            "Problem and context",
            "Practical explanation or comparison",
            "How the website solves the problem",
            "Proof, examples or transparent evidence",
            "Clear next step to the target website",
        ],
        "cta": f"Learn more at {target_url}",
    }


def queue_growth_drafts(state, target_url: str, campaign: str = "timepressure-growth") -> int:
    created = 0
    for account in state.social_accounts:
        if not account.enabled or not account.connected:
            continue
        url = campaign_url(target_url, account.platform, medium="social", campaign=campaign)
        recent = [
            p for p in state.social_posts
            if p.account_id == account.id and p.campaign == campaign and p.url == url
            and (time.time() - p.created_at) < 86400
        ]
        if recent:
            continue
        text = (
            f"Useful resource: {urlparse(target_url).netloc}. "
            "Sharing this resource for people who are actively interested in the topic."
        )
        queue_post(state, account.id, text, url, campaign)
        created += 1
    return created


def snapshot(state, config=None) -> dict:
    traffic = getattr(state, "traffic", None)
    return {
        "targetUrl": traffic.target_url if traffic else (getattr(config, "target_url", None) if config else None),
        "campaign": traffic.campaign if traffic else None,
        "verifiedVisits": traffic.verified_visits if traffic else 0,
        "targetVisits": traffic.target_visits if traffic else 0,
        "status": traffic.status if traffic else "idle",
        "plan": state.working_plan[-20:],
        "lastAnalysis": state.decision.get("siteAnalysis"),
        "lastAction": state.decision.get("action"),
        "policy": "legitimate traffic only; no fabricated engagement",
    }
