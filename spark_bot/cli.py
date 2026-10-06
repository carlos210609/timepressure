from __future__ import annotations
import argparse, json
from .agent import SparkBot

def main(argv=None):
    p = argparse.ArgumentParser(prog="sparkbot", description="Spark Bot — general agent and legitimate marketing operator")
    s = p.add_subparsers(dest="command", required=True)
    c = s.add_parser("think"); c.add_argument("objective")
    c = s.add_parser("skills"); c.add_argument("--category")
    s.add_parser("status")
    s.add_parser("policy")
    c = s.add_parser("pressure"); c.add_argument("value", type=float)
    args = p.parse_args(argv)
    bot = SparkBot()
    if args.command == "think":
        print(json.dumps(bot.think(args.objective), indent=2, ensure_ascii=False))
    elif args.command == "skills":
        print(json.dumps(bot.capabilities(args.category), indent=2, ensure_ascii=False))
    elif args.command == "status":
        print(json.dumps(bot.status(), indent=2, ensure_ascii=False))
    elif args.command == "policy":
        print(json.dumps(bot.policies(), indent=2, ensure_ascii=False))
    elif args.command == "pressure":
        if not 0 <= args.value <= 100: raise SystemExit("pressure must be between 0 and 100")
        bot.pressure = args.value
        print(f"Spark Bot pressure: {bot.pressure:.0f}/100")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
