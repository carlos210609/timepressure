"""Social Traffic Engine for TimePressure.

Plans and tracks legitimate social promotion. It never creates fake accounts,
mass-registers identities, sends unsolicited bulk replies, or fabricates metrics.
Publishing adapters require an explicitly connected account/token.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field

PLATFORMS = ("x", "facebook", "instagram", "reddit", "tiktok", "youtube")


@dataclass
class SocialAccount:
    id: str
    platform: str
    handle: str
    account_ref: str
    connected: bool = False
    enabled: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class SocialPost:
    id: str
    account_id: str
    platform: str
    text: str
    url: str
    campaign: str
    status: str = "draft"
    published_at: float | None = None
    external_id: str | None = None
    clicks: int = 0
    visits: int = 0
    created_at: float = field(default_factory=time.time)


def register_account(state, platform: str, handle: str, account_ref: str, connected: bool = False):
    platform = platform.lower().strip()
    if platform not in PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")
    if not handle.strip() or not account_ref.strip():
        raise ValueError("handle and account_ref are required")
    account = SocialAccount(str(uuid.uuid4()), platform, handle.strip(), account_ref.strip(), connected)
    state.social_accounts.append(account)
    return account


def queue_post(state, account_id: str, text: str, url: str, campaign: str):
    account = next((a for a in state.social_accounts if a.id == account_id), None)
    if not account:
        raise ValueError("Social account not found")
    if not account.enabled:
        raise ValueError("Social account is disabled")
    if not text.strip():
        raise ValueError("Post text cannot be empty")
    post = SocialPost(str(uuid.uuid4()), account.id, account.platform, text.strip(), url, campaign.strip() or "timepressure")
    state.social_posts.append(post)
    state.social_posts = state.social_posts[-5000:]
    return post


def approve_post(state, post_id: str):
    post = next((p for p in state.social_posts if p.id == post_id), None)
    if not post:
        raise ValueError("Social post not found")
    if post.status != "draft":
        raise ValueError(f"Post is already {post.status}")
    post.status = "approved"
    return post


def mark_published(state, post_id: str, external_id: str | None = None):
    post = next((p for p in state.social_posts if p.id == post_id), None)
    if not post:
        raise ValueError("Social post not found")
    if post.status not in ("approved", "queued"):
        raise ValueError("Post must be approved before publishing")
    post.status = "published"
    post.published_at = time.time()
    post.external_id = external_id
    return post


def record_metrics(state, post_id: str, clicks: int = 0, visits: int = 0):
    post = next((p for p in state.social_posts if p.id == post_id), None)
    if not post:
        raise ValueError("Social post not found")
    if clicks < 0 or visits < 0:
        raise ValueError("Metrics cannot be negative")
    post.clicks += clicks
    post.visits += visits
    return post


def social_snapshot(state):
    accounts = [asdict(a) for a in state.social_accounts]
    posts = [asdict(p) for p in state.social_posts[-100:]]
    published = [p for p in state.social_posts if p.status == "published"]
    return {
        "accounts": accounts,
        "posts": posts,
        "totals": {
            "accounts": len(accounts),
            "connected": sum(a["connected"] and a["enabled"] for a in accounts),
            "published": len(published),
            "clicks": sum(p["clicks"] for p in published),
            "visits": sum(p["visits"] for p in published),
        },
    }
