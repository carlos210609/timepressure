"""Discover legitimate, public revenue opportunities without submitting or spending money."""

import json
import re
import time
import urllib.parse
import urllib.request

REWARD_RE = re.compile(r"(?:\$|USD\s*)(\d+(?:\.\d{1,2})?)", re.I)


def _get_json(url, timeout=10):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "TimePressure/0.4",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _estimate_reward(text):
    values = [float(x) for x in REWARD_RE.findall(text or "")]
    return max(values, default=0.0)


def discover_github_bounties(limit=12):
    query = urllib.parse.quote('label:bounty is:issue is:open no:assignee')
    data = _get_json(
        f"https://api.github.com/search/issues?q={query}&sort=updated&order=desc&per_page={limit}"
    )
    opportunities = []
    for item in data.get("items", []):
        body = item.get("body") or ""
        title = item.get("title") or ""
        reward = _estimate_reward(title + "\n" + body)
        opportunities.append({
            "id": f"github:{item.get('repository_url','')}#{item.get('number')}",
            "source": "github_bounty",
            "title": title,
            "url": item.get("html_url"),
            "rewardUsd": reward,
            "score": round((reward or 1.0) * (1.2 if reward else 0.6), 2),
            "status": "open",
            "discoveredAt": time.time(),
            "instruction": "Inspect scope, acceptance criteria and payment terms. Do not submit or claim work without authorization.",
        })
    return opportunities


def discover(config, limit=12):
    if not config.allow_network:
        return []
    found = []
    try:
        found.extend(discover_github_bounties(limit))
    except Exception:
        pass
    return sorted(found, key=lambda x: x["score"], reverse=True)[:limit]
