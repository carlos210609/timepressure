#!/usr/bin/env python3
"""CLI entry point for TimePressure's Marketplace Hub."""
from __future__ import annotations
import argparse
import json
from marketplace_hub import discover_all, execute_task, snapshot


def main(argv=None):
    p = argparse.ArgumentParser(description="TimePressure Marketplace Hub")
    sub = p.add_subparsers(dest="cmd", required=True)
    scan = sub.add_parser("scan", help="Scan all configured marketplaces.")
    scan.add_argument("--limit", type=int, default=10)
    sub.add_parser("status", help="Show marketplace connector status.")
    run = sub.add_parser("execute", help="Execute through an explicitly configured official bridge.")
    run.add_argument("marketplace")
    run.add_argument("task_id")
    run.add_argument("instruction")
    args = p.parse_args(argv)

    if args.cmd == "status":
        print(json.dumps({"marketplaces": snapshot()}, indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "scan":
        tasks, errors = discover_all(args.limit)
        print(json.dumps({
            "tasks": [dict(vars(x), score=__import__("marketplace_hub").score(x)) for x in tasks],
            "errors": errors,
        }, indent=2, ensure_ascii=False))
        return 0
    result = execute_task(args.marketplace, args.task_id, args.instruction)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
