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
        _print_json(_status_payload(agent.state, agent.oauth))
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
        description="TimePressure — open-source autonomous agent runtime driven by time pressure.",
    )
    parser.add_argument("--version", action="version", version="TimePressure 0.5.0")
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


    revenue = sub.add_parser("revenue", help="Record verified revenue.")
    revenue_sub = revenue.add_subparsers(dest="sub", required=True)
    add = revenue_sub.add_parser("add", help="Add a revenue event to the local ledger.")
    add.add_argument("usd", type=float)
    add.add_argument("--source", default="manual")
    add.add_argument("--reference")
    add.add_argument("--strategy", help="Strategy id to update the learning statistics.")

    wallet = sub.add_parser("wallet", help="Manage Litecoin Core RPC operations.")
    wallet_sub = wallet.add_subparsers(dest="sub", required=True)
    wallet_sub.add_parser("balance")
    address = wallet_sub.add_parser("address")
    address.add_argument("label", nargs="?", default="timepressure")
    payout = wallet_sub.add_parser("payout")
    payout.add_argument("ltc", type=float)
    payout.add_argument("address", nargs="?")
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
                _print_json(_status_payload(state, oauth))
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

        if args.cmd == "reset":
            state.pressure = reset_cycle(state.pressure, time.time(), config.cycle_ms)
            store.save(state)
            print("✓ Cycle reset.")
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
                print(f"{rpc.balance()} LTC")
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
