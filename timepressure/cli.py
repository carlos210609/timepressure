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


def main():
    config = load_config()
    store = Store(config.data_dir)
    state = store.init(config.target_cents, config.cycle_ms)

    parser = argparse.ArgumentParser(prog="timepressure")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("run")
    sub.add_parser("status")
    sub.add_parser("pressure")
    sub.add_parser("doctor")
    sub.add_parser("reset")

    revenue = sub.add_parser("revenue")
    revenue_sub = revenue.add_subparsers(dest="sub")
    add = revenue_sub.add_parser("add")
    add.add_argument("usd", type=float)
    add.add_argument("--source", default="manual")
    add.add_argument("--reference")

    wallet = sub.add_parser("wallet")
    wallet_sub = wallet.add_subparsers(dest="sub")
    wallet_sub.add_parser("balance")
    address = wallet_sub.add_parser("address")
    address.add_argument("label", nargs="?", default="timepressure")
    payout = wallet_sub.add_parser("payout")
    payout.add_argument("ltc", type=float)
    payout.add_argument("address", nargs="?")
    quote = wallet_sub.add_parser("quote")
    quote.add_argument("usd", type=float)
    quote.add_argument("rate", type=float)

    args = parser.parse_args()

    if args.cmd is None:
        from .gui import launch
        launch()
        return 0

    try:
        if args.cmd in ("status", "pressure"):
            state.pressure = calculate_pressure(time.time(), state.pressure)
            store.save(state)
            print(json.dumps({
                "status": state.pressure.status,
                "pressure": f"{state.pressure.pressure:.1f}%",
                "cycleRevenue": f"USD {state.pressure.cycle_revenue_cents/100:.2f}",
                "target": f"USD {state.pressure.target_cents/100:.2f}",
                "deadline": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(state.pressure.deadline)),
            }, indent=2))
            return 0

        if args.cmd == "doctor":
            from .oauth import OAuth
            print(json.dumps({
                "python": sys.version.split()[0],
                "dataDir": config.data_dir,
                "modelConfigured": bool(config.api_key),
                "chatgptOAuth": OAuth().connected(),
                "networkEnabled": config.allow_network,
                "target": f"USD {config.target_cents/100:.2f}",
                "cycleMs": config.cycle_ms,
                "litecoinRpc": config.ltc_rpc_url,
                "payoutAddressConfigured": bool(config.ltc_payout_address),
                "autoPayout": config.ltc_auto_payout,
                "browserEnabled": config.browser_enabled,
                "browserHeadless": config.browser_headless,
                "browserAllowedDomains": config.browser_allowed_domains,
            }, indent=2))
            return 0

        if args.cmd == "reset":
            state.pressure = reset_cycle(state.pressure, time.time(), config.cycle_ms)
            store.save(state)
            print("Cycle reset.")
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
            print(f"Recorded USD {cents/100:.2f} from {args.source}. Status: {state.pressure.status}")
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
                print(json.dumps({
                    "usd": args.usd,
                    "ltcUsd": args.rate,
                    "ltc": usd_to_ltc(args.usd, args.rate),
                }, indent=2))
                return 0
            if args.sub == "payout":
                target = args.address or config.ltc_payout_address
                if not target:
                    raise ValueError("Set LTC_PAYOUT_ADDRESS or pass an address.")
                if args.ltc <= 0:
                    raise ValueError("Payout amount must be positive.")
                if rpc.balance() < args.ltc:
                    raise ValueError("Insufficient LTC balance.")
                print(json.dumps({
                    "txid": rpc.send(target, args.ltc),
                    "address": target,
                    "amountLtc": args.ltc,
                }, indent=2))
                return 0

        if args.cmd == "run":
            print("TimePressure running. Ctrl+C to stop.")
            agent = Agent(config, store, state)
            while True:
                agent.tick()
                p = agent.state.pressure
                print(
                    f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] "
                    f"{p.status} pressure={p.pressure:.1f}% revenue=USD {p.cycle_revenue_cents/100:.2f}",
                    flush=True,
                )
                if p.status == "dead":
                    print("DEAD: revenue target was missed.")
                    return 2
                time.sleep(config.tick_ms / 1000)

        parser.print_help()
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
