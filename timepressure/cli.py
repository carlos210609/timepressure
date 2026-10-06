import argparse
import json
import os
import sys
import time
import uuid

from .agent import Agent
from .config import load_config
from .litecoin import LitecoinRPC, usd_to_ltc
from .models import RevenueEvent
from .pressure import calculate_pressure, record_revenue, reset_cycle
from .store import Store
from .opportunity_hunter import discover
from .task_engine import TaskPortfolio
from .security import security_snapshot
from .traffic import campaign_url, record_visit, start_campaign, traffic_snapshot
from .social import approve_post, mark_published, queue_post, record_metrics, register_account, social_snapshot
from .innovation import intelligence_snapshot
from .revenue import RevenueOpportunity, RevenueAttempt, select_next_opportunity, start_attempt, complete_attempt, revenue_snapshot, score_revenue_opportunity
from okx_ai import discover as marketplace_discover, snapshot as marketplace_snapshot, score as marketplace_score
from marketplace_accounts import public_status as marketplace_account_status
from .health import system_health


def _status_payload(state, config):
    now = time.time()
    state.pressure = calculate_pressure(now, state.pressure)
    p = state.pressure
    return {
        "status": p.status,
        "pressure": round(p.pressure, 1),
        "cycleRevenueUsd": round(p.cycle_revenue_cents / 100, 2),
        "targetUsd": round(p.target_cents / 100, 2),
        "secondsLeft": max(0, int(p.deadline - now)),
        "deadline": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.deadline)),
        "nvidia": bool(config.nvidia_api_key),
        "lastThought": state.last_thought,
        "traffic": traffic_snapshot(state),
        "social": social_snapshot(state),
        "intelligence": intelligence_snapshot(state, config),
        "marketplaces": marketplace_snapshot(),
        "marketplaceTasks": state.marketplace_tasks[:20],
        "marketplaceErrors": state.marketplace_errors[:10],
        "marketplaceAccounts": marketplace_account_status(),
        "health": system_health(marketplace_account_status(), state),
    }


def _print_json(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def _run_agent(config, store, state, once=False):
    if state.pressure.status == "dead":
        print("Agent is dead. Run timepressure reset before starting again.", file=sys.stderr)
        return 2
    agent = Agent(config, store, state)
    if once:
        agent.tick()
        _print_json(_status_payload(agent.state, config))
        return 0
    print("TimePressure agent running. Press Ctrl+C to stop.")
    print("Use timepressure status --watch in another terminal to monitor it.")
    try:
        while True:
            agent.tick()
            p = agent.state.pressure
            print(
                f"[{time.strftime('%H:%M:%S')}] "
                f"{p.status.upper():8} pressure={p.pressure:5.1f}% "
                f"revenue=USD {p.cycle_revenue_cents / 100:.2f}/{p.target_cents / 100:.2f} "
                f"left={max(0, int(p.deadline - time.time()))}s",
                flush=True,
            )
            if p.status == "dead":
                print("DEAD: revenue target was missed.", file=sys.stderr)
                return 2
            time.sleep(max(0.2, config.tick_ms / 1000))
    except KeyboardInterrupt:
        print("\nStopped.")
        return 130


def build_parser():
    parser = argparse.ArgumentParser(
        prog="timepressure",
        description="TimePressure — autonomous OKX.AI Task Marketplace agent driven by time pressure.",
    )
    parser.add_argument("--version", action="version", version="TimePressure 1.0.0")
    sub = parser.add_subparsers(dest="cmd")

    run = sub.add_parser("run", help="Run the autonomous agent continuously.")
    run.add_argument("--once", action="store_true", help="Run one agent tick and exit.")
    run.add_argument("--web", action="store_true", help="Run the local monitoring dashboard alongside the agent.")

    status = sub.add_parser("status", help="Show current agent state.")
    status.add_argument("--watch", action="store_true", help="Refresh status continuously.")
    status.add_argument("--interval", type=float, default=2.0)

    sub.add_parser("pressure", help="Show the current pressure state.")
    sub.add_parser("doctor", help="Check the local runtime configuration.")
    web = sub.add_parser("web", help="Open the local OpenCloud-style monitoring dashboard.")
    web.add_argument("--host", default=None)
    web.add_argument("--port", type=int, default=8787)
    sub.add_parser("reset", help="Reset the current survival cycle.")
    sub.add_parser("hunt", help="Discover public paid opportunities and queue the best ones.")
    sub.add_parser("tasks", help="Show active multitask opportunities and learned strategy stats.")
    marketplaces = sub.add_parser("marketplaces", help="Scan and rank work on the OKX.AI Task Marketplace.")
    marketplaces.add_argument("--limit", type=int, default=10, help="Maximum OKX.AI tasks to inspect.")

    traffic = sub.add_parser("traffic", help="Run a legitimate website traffic campaign.")
    traffic_sub = traffic.add_subparsers(dest="sub", required=True)
    traffic_start = traffic_sub.add_parser("start", help="Start a traffic campaign.")
    traffic_start.add_argument("url")
    traffic_start.add_argument("target", type=int, help="Target number of verified visits.")
    traffic_start.add_argument("--campaign", default="timepressure")
    traffic_status = traffic_sub.add_parser("status", help="Show traffic campaign status.")
    traffic_link = traffic_sub.add_parser("link", help="Create a tracked UTM campaign URL.")
    traffic_link.add_argument("source")
    traffic_link.add_argument("--medium", default="traffic")
    traffic_link.add_argument("--campaign", default=None)
    traffic_record = traffic_sub.add_parser("record", help="Record externally verified visits.")
    traffic_record.add_argument("source")
    traffic_record.add_argument("visits", type=int, default=1, nargs="?")
    traffic_record.add_argument("--reference")

    social = sub.add_parser("social", help="Manage legitimate social traffic campaigns.")
    social_sub = social.add_subparsers(dest="sub", required=True)
    sa = social_sub.add_parser("account", help="Register an owned/authorized social account.")
    sa.add_argument("platform", choices=["x", "facebook", "instagram", "reddit", "tiktok", "youtube"])
    sa.add_argument("handle")
    sa.add_argument("account_ref", help="Provider account/page identifier or connection reference.")
    sa.add_argument("--connected", action="store_true")
    social_sub.add_parser("status", help="Show social campaign status.")
    sp = social_sub.add_parser("queue", help="Queue a post for an authorized account.")
    sp.add_argument("account_id")
    sp.add_argument("text")
    sp.add_argument("url")
    sp.add_argument("--campaign", default="timepressure")
    sap = social_sub.add_parser("approve", help="Approve a draft before publishing.")
    sap.add_argument("post_id")
    spp = social_sub.add_parser("published", help="Mark a provider-confirmed publication.")
    spp.add_argument("post_id")
    spp.add_argument("--external-id")
    sm = social_sub.add_parser("metrics", help="Record provider analytics.")
    sm.add_argument("post_id")
    sm.add_argument("--clicks", type=int, default=0)
    sm.add_argument("--visits", type=int, default=0)


    revenue = sub.add_parser("revenue", help="Revenue Engine and verified revenue ledger.")
    revenue_sub = revenue.add_subparsers(dest="sub", required=True)
    revenue_sub.add_parser("engine", help="Show Revenue Engine ranking and verified P&L.")
    revenue_sub.add_parser("next", help="Select the highest expected-value opportunity.")
    ra = revenue_sub.add_parser("attempt", help="Start an attempt for the selected opportunity.")
    ra.add_argument("opportunity_id", nargs="?")
    rf = revenue_sub.add_parser("finish", help="Finish an attempt.")
    rf.add_argument("attempt_id")
    rf.add_argument("--revenue-usd", type=float, default=0.0)
    rf.add_argument("--cost-usd", type=float, default=0.0)
    rf.add_argument("--reference")
    add = revenue_sub.add_parser("add", help="Add a revenue event to the local ledger.")
    add.add_argument("usd", type=float)
    add.add_argument("--source", default="manual")
    add.add_argument("--reference")
    add.add_argument("--strategy", help="Strategy id to update the learning statistics.")

    wallet = sub.add_parser("wallet", help="Manage Litecoin Core RPC operations.")
    wallet_sub = wallet.add_subparsers(dest="sub", required=True)
    wallet_sub.add_parser("balance")
    wallet_sub.add_parser("info")
    wallet_sub.add_parser("transactions")
    address = wallet_sub.add_parser("address", aliases=["receive"])
    address.add_argument("label", nargs="?", default="timepressure")
    payout = wallet_sub.add_parser("payout")
    payout.add_argument("ltc", type=float)
    payout.add_argument("address", nargs="?")
    validate = wallet_sub.add_parser("validate")
    validate.add_argument("address")
    quote = wallet_sub.add_parser("quote")
    quote.add_argument("usd", type=float)
    quote.add_argument("rate", type=float)

    browser = sub.add_parser("browser", help="Use the configured browser automation.")
    browser_sub = browser.add_subparsers(dest="sub", required=True)
    open_cmd = browser_sub.add_parser("open", help="Open an allowed HTTPS URL.")
    open_cmd.add_argument("url")
    return parser


def main(argv=None):
    config = load_config()
    store = Store(config.data_dir)
    state = store.init(config.target_cents, config.cycle_ms)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd is None:
        parser.print_help()
        print("\nQuick start:")
        print("  timepressure auth login")
        print("  timepressure doctor")
        print("  timepressure run")
        return 0

    try:
        if args.cmd in ("status", "pressure"):
            if not getattr(args, "watch", False):
                _print_json(_status_payload(state, config))
                return 0
            while True:
                print("\033[2J\033[H", end="")
                _print_json(_status_payload(state, config))
                time.sleep(max(0.5, args.interval))

        if args.cmd == "doctor":
            _print_json({
                "python": sys.version.split()[0],
                "version": "0.5.0",
                "dataDir": config.data_dir,
                "nvidiaConfigured": bool(config.nvidia_api_key),
                "aiProvider": config.ai_provider,
                "networkEnabled": config.allow_network,
                "browserEnabled": config.browser_enabled,
                "browserHeadless": config.browser_headless,
                "browserAllowedDomains": config.browser_allowed_domains,
                "temporaryEmailEnabled": config.temp_email_enabled,
                "temporaryEmailTargetDomains": config.temp_email_target_domains,
                "targetUsd": config.target_cents / 100,
                "cycleMs": config.cycle_ms,
                "tickMs": config.tick_ms,
                "litecoinRpc": config.ltc_rpc_url,
                "payoutAddressConfigured": bool(config.ltc_payout_address),
                "security": security_snapshot(config),
                "traffic": traffic_snapshot(state),
            })
            return 0


        if args.cmd == "hunt":
            opportunities = discover(config, limit=12)
            portfolio = TaskPortfolio(config.data_dir)
            tasks = portfolio.add_opportunities(opportunities, max_active=6)
            _print_json({"discovered": opportunities, "activeTasks": tasks})
            return 0

        if args.cmd == "tasks":
            portfolio = TaskPortfolio(config.data_dir)
            _print_json({"active": portfolio.snapshot(), "strategyStats": portfolio.stats_snapshot()})
            return 0

        if args.cmd == "marketplaces":
            orchestrator = Orchestrator(state, store)
            tasks = orchestrator.discover(max(1, min(args.limit, 50)))
            _print_json({
                "marketplaces": marketplace_snapshot(),
                "accounts": marketplace_account_status(),
                "tasks": [dict(vars(x), score=marketplace_score(x)) for x in tasks],
                "errors": state.marketplace_errors,
                "decision": state.decision,
                "learning": state.learning,
                "health": system_health(marketplace_account_status(), state),
            })
            return 0

        if args.cmd == "traffic":
            if args.sub == "start":
                campaign = start_campaign(state, args.url, args.target, args.campaign)
                store.save(state)
                _print_json({"started": True, **traffic_snapshot(state)})
                return 0
            if args.sub == "status":
                _print_json(traffic_snapshot(state))
                return 0
            if args.sub == "link":
                if not state.traffic:
                    raise ValueError("Start a traffic campaign first.")
                print(campaign_url(state.traffic.target_url, args.source, args.medium, args.campaign or state.traffic.campaign))
                return 0
            if args.sub == "record":
                event = record_visit(state, args.source, args.visits, args.reference)
                store.save(state)
                _print_json({"recorded": vars(event), "campaign": traffic_snapshot(state)})
                return 0

        if args.cmd == "social":
            if args.sub == "account":
                account = register_account(state, args.platform, args.handle, args.account_ref, args.connected)
            elif args.sub == "status":
                _print_json(social_snapshot(state)); return 0
            elif args.sub == "queue":
                post = queue_post(state, args.account_id, args.text, args.url, args.campaign)
            elif args.sub == "approve":
                post = approve_post(state, args.post_id)
            elif args.sub == "published":
                post = mark_published(state, args.post_id, args.external_id)
            elif args.sub == "metrics":
                post = record_metrics(state, args.post_id, args.clicks, args.visits)
            store.save(state)
            _print_json(vars(account if args.sub == "account" else post) if args.sub != "status" else social_snapshot(state))
            return 0

        if args.cmd == "reset":
            state.pressure = reset_cycle(state.pressure, time.time(), config.cycle_ms)
            store.save(state)
            print("✓ Cycle reset.")
            return 0

        if args.cmd == "revenue" and args.sub in ("engine", "next", "attempt", "finish"):
            raw = []
            for item in state.revenue_opportunities:
                try:
                    raw.append(RevenueOpportunity(**{k: item[k] for k in RevenueOpportunity.__dataclass_fields__}))
                except (KeyError, TypeError, ValueError):
                    continue
            if args.sub == "engine":
                ranked = []
                for item in raw:
                    score = score_revenue_opportunity(item)
                    ranked.append({**vars(item), **score})
                ranked.sort(key=lambda x: x["score"], reverse=True)
                attempts = [RevenueAttempt(**x) for x in state.revenue_attempts]
                _print_json({"engine": revenue_snapshot(raw, attempts, sum(x.cents for x in state.revenue)), "ranked": ranked[:20]})
                return 0
            if args.sub == "next":
                selected = select_next_opportunity(raw)
                if not selected:
                    _print_json({"selected": None, "reason": "no eligible opportunity"})
                    return 0
                for item in state.revenue_opportunities:
                    if item.get("id") == selected.id:
                        item["status"] = selected.status
                store.save(state)
                _print_json({"selected": vars(selected), "score": score_revenue_opportunity(selected)})
                return 0
            if args.sub == "attempt":
                target = next((x for x in raw if x.id == args.opportunity_id), None) if args.opportunity_id else select_next_opportunity(raw)
                if not target:
                    raise ValueError("No eligible opportunity.")
                attempt = start_attempt(target)
                for item in state.revenue_opportunities:
                    if item.get("id") == target.id:
                        item["status"] = "active"
                state.revenue_attempts.append(vars(attempt))
                store.save(state)
                _print_json({"attempt": vars(attempt), "opportunity": vars(target), "score": score_revenue_opportunity(target)})
                return 0
            attempt_data = next((x for x in state.revenue_attempts if x.get("id") == args.attempt_id), None)
            if not attempt_data:
                raise ValueError("Unknown attempt.")
            attempt = RevenueAttempt(**attempt_data)
            if attempt.status != "active":
                raise ValueError("Attempt is not active.")
            finished = complete_attempt(attempt, round(args.revenue_usd * 100), round(args.cost_usd * 100), args.reference)
            attempt_data.update(vars(finished))
            state.revenue_cost_cents += finished.cost_cents
            store.save(state)
            _print_json({"attempt": vars(finished), "verifiedRevenueRecorded": False, "message": "Only revenue add with a provider-confirmed payment reference enters the verified ledger."})
            return 0

        if args.cmd == "revenue" and args.sub == "add":
            cents = round(args.usd * 100)
            if cents <= 0:
                raise ValueError("Amount must be positive.")
            reference = args.reference or str(uuid.uuid4())
            if any(item.reference == reference for item in state.revenue):
                raise ValueError("Duplicate revenue reference.")
            timestamp = time.time()
            state.pressure = calculate_pressure(timestamp, state.pressure)
            event = RevenueEvent(str(uuid.uuid4()), cents, args.source, reference, timestamp)
            state.pressure = record_revenue(state.pressure, cents, timestamp)
            store.add_revenue(state, event)
            if args.strategy:
                TaskPortfolio(config.data_dir).record_revenue(args.strategy, args.usd)
            store.save(state)
            print(f"✓ Recorded USD {cents / 100:.2f} from {args.source}. Status: {state.pressure.status}")
            return 0

        if args.cmd == "wallet":
            rpc = LitecoinRPC(config)
            if args.sub == "balance":
                _print_json({"ltc": rpc.balance(), "balances": rpc.balances()})
                return 0
            if args.sub == "info":
                _print_json({"wallet": rpc.wallet_info(), "blockchain": rpc.blockchain_info()})
                return 0
            if args.sub == "transactions":
                _print_json(rpc.transactions())
                return 0
            if args.sub == "validate":
                _print_json(rpc.validate_address(args.address))
                return 0
            if args.sub == "address":
                print(rpc.new_address(args.label))
                return 0
            if args.sub == "quote":
                _print_json({"usd": args.usd, "ltcUsd": args.rate, "ltc": usd_to_ltc(args.usd, args.rate)})
                return 0
            if args.sub == "payout":
                if os.getenv("TIMEPRESSURE_ALLOW_PAYOUT", "false").lower() != "true":
                    raise PermissionError("Payouts are disabled. Set TIMEPRESSURE_ALLOW_PAYOUT=true for an explicit operator action.")
                target = args.address or config.ltc_payout_address
                if not target:
                    raise ValueError("Set LTC_PAYOUT_ADDRESS or pass an address.")
                if args.ltc <= 0:
                    raise ValueError("Payout amount must be positive.")
                if args.ltc < config.ltc_min_payout:
                    raise ValueError(f"Payout is below LTC_MIN_PAYOUT ({config.ltc_min_payout:g} LTC).")
                if rpc.balance() < args.ltc:
                    raise ValueError("Insufficient LTC balance.")
                _print_json({"txid": rpc.send(target, args.ltc), "address": target, "amountLtc": args.ltc})
                return 0

        if args.cmd == "browser" and args.sub == "open":
            from .tools import run_tool
            print(json.dumps(run_tool("browser_open", args.url, config, state, store), indent=2, ensure_ascii=False))
            return 0

        if args.cmd == "web":
            from .web import serve
            serve(config, store, state, host=args.host, port=args.port)
            return 0

        if args.cmd == "run":
            if args.web:
                from .web import serve
                import threading
                web_host = os.getenv("TIMEPRESSURE_WEB_HOST")
                web_port = int(os.getenv("TIMEPRESSURE_WEB_PORT", "8787"))
                threading.Thread(
                    target=serve,
                    args=(config, store, state, web_host, web_port),
                    daemon=True,
                ).start()
            return _run_agent(config, store, state, args.once)

        parser.print_help()
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
