"""Legitimate traffic campaign utilities for TimePressure.

Traffic Mode never fabricates visits, clicks, impressions, or ad engagement.
It prepares trackable campaign URLs and records only externally verified visits.
"""
from __future__ import annotations
import time
import uuid
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from .security import assert_https_public_url
from .models import TrafficEvent, TrafficState

def campaign_url(target_url: str, source: str, medium: str = "traffic", campaign: str = "timepressure") -> str:
    parsed = assert_https_public_url(target_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({"utm_source": source.strip() or "timepressure", "utm_medium": medium.strip() or "traffic", "utm_campaign": campaign.strip() or "timepressure"})
    return urlunparse(parsed._replace(query=urlencode(query)))

def start_campaign(state, target_url: str, target_visits: int, campaign: str) -> TrafficState:
    if target_visits <= 0:
        raise ValueError("Traffic target must be positive.")
    assert_https_public_url(target_url)
    state.traffic = TrafficState(str(uuid.uuid4()), target_url, campaign, target_visits, 0, time.time(), "active")
    state.working_goal = f"Increase legitimate traffic to {target_url}"
    return state.traffic

def record_visit(state, source: str, visits: int = 1, reference: str | None = None):
    if not getattr(state, "traffic", None):
        raise ValueError("No traffic campaign is active. Run traffic start first.")
    if visits <= 0:
        raise ValueError("Visit count must be positive.")
    ref = reference or str(uuid.uuid4())
    if any(e.reference == ref for e in state.traffic_events):
        raise ValueError("Duplicate traffic event reference.")
    event = TrafficEvent(str(uuid.uuid4()), visits, source or "unknown", ref, time.time())
    state.traffic_events.append(event)
    state.traffic_events = state.traffic_events[-5000:]
    state.traffic.verified_visits += visits
    if state.traffic.verified_visits >= state.traffic.target_visits:
        state.traffic.status = "completed"
    return event

def traffic_snapshot(state):
    traffic = getattr(state, "traffic", None)
    if not traffic:
        return {"active": False}
    return {"active": True, **vars(traffic), "remaining": max(0, traffic.target_visits - traffic.verified_visits), "progress": round(min(100.0, traffic.verified_visits / max(1, traffic.target_visits) * 100), 1), "events": [vars(x) for x in state.traffic_events[-100:]]}
