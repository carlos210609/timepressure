import argparse
import json
import sys
import time
import uuid

from .agent import Agent
from .config import load_config
from .litecoin import LitecoinRPC, usd_to_ltc
from .models import RevenueEvent
from .pressure import calculate_pressure, record_revenue, reset_cycle
from .store import Store


def _status_payload(state, oauth):
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
        "chatgpt": oauth.connected(),
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
    parser.add_argument("--version", action="version", version="TimePressure 0.4.0")
    sub = parser.add_subparsers(dest="cmd")

    run = sub.add_parser("run", help="Run the autonomous agent continuously.")
    run.add_argument("--once", action="store_true", help="Run one agent tick and exit.")

    status = sub.add_parser("status", help="Show current agent state.")
    status.add_argument("--watch", action="store_true", help="Refresh status continuously.")
    status.add_argument("--interval", type=float, default=2.0)

    sub.add_parser("pressure", help="Show the current pressure state.")
    sub.add_parser("doctor", help="Check the local runtime configuration.")
    sub.add_parser("reset", help="Reset the current survival cycle.")

    auth = sub.add_parser("auth", help="Manage ChatGPT authentication.")
    auth_sub = auth.add_subparsers(dest="sub", required=True)
    auth_sub.add_parser("login", help="Open the ChatGPT OAuth login flow.")
    auth_sub.add_parser("logout", help="Remove the stored ChatGPT access token.")
    auth_sub.add_parser("status", help="Show ChatGPT authentication status.")

    revenue = sub.add_parser("revenue", help="Record verified revenue.")
    revenue_sub = revenue.add_subparsers(dest="sub", required=True)
    add = revenue_sub.add_parser("add", help="Add a revenue event to the local ledger.")
    add.add_argument("usd", type=float)
    add.add_argument("--source", default="manual")
    add.add_argument("--reference")

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
            from .oauth import OAuth
            oauth = OAuth()
            if not getattr(args, "watch", False):
                _print_json(_status_payload(state, oauth))
                return 0
            while True:
                print("\033[2J\033[H", end="")
                _print_json(_status_payload(state, oauth))
                time.sleep(max(0.5, args.interval))

        if args.cmd == "doctor":
            from .oauth import OAuth
            _print_json({
                "python": sys.version.split()[0],
                "version": "0.4.0",
                "dataDir": config.data_dir,
                "apiKeyConfigured": bool(config.api_key),
                "chatgptOAuth": OAuth().connected(),
                "networkEnabled": config.allow_network,
                "browserEnabled": config.browser_enabled,
                "browserHeadless": config.browser_headless,
                "browserAllowedDomains": config.browser_allowed_domains,
                "targetUsd": config.target_cents / 100,
                "cycleMs": config.cycle_ms,
                "tickMs": config.tick_ms,
                "litecoinRpc": config.ltc_rpc_url,
                "payoutAddressConfigured": bool(config.ltc_payout_address),
            })
            return 0

        if args.cmd == "auth":
            from .oauth import OAuth
            oauth = OAuth()
            if args.sub == "login":
                print("Opening ChatGPT login in your browser...")
                oauth.login()
                print("✓ ChatGPT connected.")
                return 0
            if args.sub == "logout":
                oauth.logout()
                print("✓ ChatGPT credentials removed.")
                return 0
            if args.sub == "status":
                _print_json({"connected": oauth.connected(), "credentialFile": str(oauth.path)})
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
            event = RevenueEvent(str(uuid.uuid4()), cents, args.source, reference, time.time())
            store.add_revenue(state, event)
            state.pressure = record_revenue(state.pressure, cents, event.timestamp)
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

        if args.cmd == "run":
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
