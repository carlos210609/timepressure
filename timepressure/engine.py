from __future__ import annotations
import re
from html import unescape
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STRATEGIES = [
    ("SEO", "improve title and search intent"),
    ("SEO", "strengthen the primary page description"),
    ("Content", "publish a useful answer to one audience question"),
    ("Content", "create a comparison or decision guide"),
    ("Community", "share a useful resource where promotion is allowed"),
    ("Social", "prepare an educational post for an authorized account"),
    ("Video", "turn one useful page into a short educational video"),
    ("Newsletter", "publish a useful update to an opted-in audience"),
    ("Partnership", "propose a relevant co-marketing resource"),
    ("PR", "pitch a genuinely newsworthy story"),
    ("Directory", "submit to a relevant legitimate directory"),
    ("Referral", "add a useful referral path for existing visitors"),
    ("Conversion", "remove friction from the main CTA"),
    ("Analytics", "measure source, engagement and conversion signals"),
    ("International", "adapt useful content for a relevant market"),
]

def validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("target URL must be a public HTTPS URL")
    host = parsed.hostname or ""
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise ValueError("private/local targets are not allowed")
    return parsed.geturl()

def fetch_site(url: str, timeout: int = 10) -> dict:
    url = validate_url(url)
    request = Request(url, headers={"User-Agent": "TimePressure/3.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status < 200 or response.status >= 400:
            raise ValueError(f"site returned HTTP {response.status}")
        body = response.read(1_000_000).decode("utf-8", errors="replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', body, re.I | re.S)
    return {
        "url": url,
        "status": response.status,
        "title": unescape(title.group(1)).strip() if title else "",
        "description": unescape(desc.group(1)).strip() if desc else "",
    }

def choose_strategy(facts: dict, pressure: float, cycle: int) -> tuple[str, str]:
    if not facts.get("title") or not facts.get("description"):
        return ("SEO", "fix missing on-page metadata before distribution")
    if pressure >= 80:
        return STRATEGIES[(cycle + 3) % len(STRATEGIES)]
    if pressure <= 25:
        return STRATEGIES[(cycle + 12) % len(STRATEGIES)]
    return STRATEGIES[(cycle + len(facts.get("title", ""))) % len(STRATEGIES)]

def build_plan(facts: dict, pressure: float, cycle: int) -> list[dict]:
    channel, tactic = choose_strategy(facts, pressure, cycle)
    return [
        {"priority": 1, "action": "analyze", "reason": "ground decisions in the real target website"},
        {"priority": 2, "action": "execute", "channel": channel, "tactic": tactic, "reason": "one focused legitimate acquisition action"},
        {"priority": 3, "action": "measure", "reason": "only verified analytics traffic counts as progress"},
    ]
