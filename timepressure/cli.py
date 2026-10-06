"""TimePressure CLI — website traffic growth only."""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
import webbrowser

from .agent import Agent
from .config import load_config
from .models import RevenueEvent
from .pressure import calculate_pressure, reset_cycle
from .store import Store
from .traffic import campaign_url, record_visit, start_campaign, traffic_snapshot
from .social import (
    approve_post,
    mark_published,
    queue_post,
    record_metrics,
    register_account,
    social_snapshot,
)
from .web import dashboard_payload, serve


def _state(config):
    store = Store(config.data_dir)
    return store, store.load()


def _print(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def _run_agent(config, store, state, once=False):
    agent = Agent(config, store, state)
    if once:
        agent.tick()
        _print(dashboard_payload(agent.state, config))
        return 0
    print("TimePressure traffic engine running. Press Ctrl+C to stop.")
    while True:
        agent.tick()
        traffic = traffic_snapshot(agent.state)
        print(
            f"[{time.strftime('%H:%M:%S')}] "
            f"pressure={agent.state.pressure.pressure:5.1f}% "
            f"verified_visits={traffic.get('verified_visits', 0)}/"
            f"{traffic.get('target_visits', 0)} "
            f"left={max(0, int(agent.state.pressure.deadline-time.time()))}s",
            flush=True,
        )
        if agent.state.pressure.status == "dead":
            print("Cycle expired; reset the cycle to continue.")
            return 2
        time.sleep(max(0.5, config.tick_ms / 1000))


def build_parser():
    p = argparse.ArgumentParser(
        prog="timepressure",
        description="TimePressure — autonomous legitimate website traffic growth engine.",
    )
    p.add_argument("--version", action="version", version="TimePressure 2.0.0")
    sub = p.add_subparsers(dest="cmd")

    start = sub.add_parser("start", help="Start the traffic engine and dashboard.")
    start.add_argument("--host", default=None)
    start.add_argument("--port", type=int, default=8787)

    run = sub.add_parser("run", help="Run the traffic engine.")
    run.add_argument("--once", action="store_true")
    run.add_argument("--web", action="store_true")
    run.add_argument("--host", default=None)
    run.add_argument("--port", type=int, default=8787)

    status = sub.add_parser("status", help="Show traffic growth status.")
    status.add_argument("--watch", action="store_true")
    status.add_argument("--interval", type=float, default=2.0)

    sub.add_parser("pressure", help="Show pressure.")
    sub.add_parser("doctor", help="Check traffic-engine configuration.")
    sub.add_parser("reset", help="Reset the current growth cycle.")
    web = sub.add_parser("web", help="Run the website traffic dashboard.")
    web.add_argument("--host", default=None)
    web.add_argument("--port", type=int, default=8787)

    traffic = sub.add_parser("traffic", help="Manage the website traffic campaign.")
    ts = traffic.add_subparsers(dest="sub", required=True)
    a = ts.add_parser("start")
    a.add_argument("url")
    a.add_argument("target", type=int)
    a.add_argument("--campaign", default="timepressure-growth")
    ts.add_parser("status")
    l = ts.add_parser("link")
    l.add_argument("source")
    l.add_argument("--medium", default="traffic")
    l.add_argument("--campaign", default="timepressure-growth")
    r = ts.add_parser("record")
    r.add_argument("source")
    r.add_argument("visits", type=int, nargs="?", default=1)
    r.add_argument("--reference")

    social = sub.add_parser("social", help="Manage authorized social distribution.")
    ss = social.add_subparsers(dest="sub", required=True)
    a = ss.add_parser("account")
    a.add_argument("platform", choices=["x", "facebook", "instagram", "reddit", "tiktok", "youtube"])
    a.add_argument("handle")
    a.add_argument("account_ref")
    a.add_argument("--connected", action="store_true")
    ss.add_parser("status")
    q = ss.add_parser("queue")
    q.add_argument("account_id")
    q.add_argument("text")
    q.add_argument("url")
    q.add_argument("--campaign", default="timepressure-growth")
    ap = ss.add_parser("approve")
    ap.add_argument("post_id")
    pub = ss.add_parser("published")
    pub.add_argument("post_id")
    pub.add_argument("--external-id")
    m = ss.add_parser("metrics")
    m.add_argument("post_id")
    m.add_argument("--clicks", type=int, default=0)
    m.add_argument("--visits", type=int, default=0)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    config = load_config()
    store, state = _state(config)

    if args.cmd in (None, "start"):
        if not config.nvidia_api_key:
            print("NVIDIA_API_KEY is required.")
            return 2
        if not (state.target_url or config.target_url or state.traffic):
            print("Configure TIMEPRESSURE_TARGET_URL or run: python3 timepressure.py traffic start https://example.com 100")
            return 2
        if args.cmd == "start":
            thread = threading.Thread(
                target=serve,
                args=(config, store, state, args.host, args.port),
                daemon=True,
            )
            thread.start()
            url = f"http://127.0.0.1:{args.port}"
            print(f"Dashboard: {url}")
            try:
                webbrowser.open(url)
            except Exception:
                pass
        return _run_agent(config, store, state)

    if args.cmd == "run":
        if args.web:
            threading.Thread(
                target=serve,
                args=(config, store, state, args.host, args.port),
                daemon=True,
            ).start()
        return _run_agent(config, store, state, args.once)

    if args.cmd == "status":
        while True:
            _print(dashboard_payload(state, config))
            if not args.watch:
                return 0
            time.sleep(max(0.2, args.interval))

    if args.cmd == "pressure":
        state.pressure = calculate_pressure(time.time(), state.pressure, config.pressure_multiplier)
        _print({
            "pressure": round(state.pressure.pressure, 1),
            "status": state.pressure.status,
            "multiplier": config.pressure_multiplier,
        })
        return 0

    if args.cmd == "doctor":
        _print({
            "nvidiaConfigured": bool(config.nvidia_api_key),
            "targetUrl": state.target_url or config.target_url,
            "networkEnabled": config.allow_network,
            "browserEnabled": config.browser_enabled,
            "mode": "website-traffic-only",
            "policy": "no fabricated visits/clicks/impressions",
        })
        return 0

    if args.cmd == "reset":
        state.pressure = reset_cycle(state.pressure, time.time(), config.cycle_ms)
        store.save(state)
        print("Growth cycle reset.")
        return 0

    if args.cmd == "web":
        serve(config, store, state, args.host, args.port)
        return 0

    if args.cmd == "traffic":
        if args.sub == "start":
            start_campaign(state, args.url, args.target, args.campaign)
            state.target_url = args.url
            store.save(state)
            _print(traffic_snapshot(state))
            return 0
        if args.sub == "status":
            _print(traffic_snapshot(state))
            return 0
        if args.sub == "link":
            _print({"url": campaign_url(args.url if hasattr(args, "url") else (state.target_url or config.target_url), args.source, args.medium, args.campaign)})
            return 0
        if args.sub == "record":
            event = record_visit(state, args.source, args.visits, args.reference)
            store.save(state)
            _print(vars(event))
            return 0

    if args.cmd == "social":
        if args.sub == "account":
            item = register_account(state, args.platform, args.handle, args.account_ref, args.connected)
        elif args.sub == "status":
            _print(social_snapshot(state)); return 0
        elif args.sub == "queue":
            item = queue_post(state, args.account_id, args.text, args.url, args.campaign)
        elif args.sub == "approve":
            item = approve_post(state, args.post_id)
        elif args.sub == "published":
            item = mark_published(state, args.post_id, args.external_id)
        else:
            item = record_metrics(state, args.post_id, args.clicks, args.visits)
        store.save(state)
        _print(vars(item) if hasattr(item, "__dict__") else item)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
