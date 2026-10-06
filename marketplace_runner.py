#!/usr/bin/env python3
"""CLI entry point for TimePressure's OKX.AI Task Marketplace integration."""
from __future__ import annotations
import argparse
import json
from okx_ai import discover, execute_task, run_once, score, snapshot


def main(argv=None):
    p = argparse.ArgumentParser(description="TimePressure — OKX.AI Task Marketplace agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="Discover OKX.AI tasks.")
    scan.add_argument("--limit", type=int, default=10)

    sub.add_parser("status", help="Show OKX.AI connection mode.")

    run = sub.add_parser("execute", help="Execute a task through the configured official bridge.")
    run.add_argument("task_id")
    run.add_argument("instruction")

    args = p.parse_args(argv)

    if args.cmd == "status":
        print(json.dumps({"marketplaces": snapshot()}, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "scan":
        tasks = discover(args.limit)
        print(json.dumps({
            "tasks": [dict(vars(x), score=score(x)) for x in tasks],
        }, indent=2, ensure_ascii=False))
        return 0

    task = next((x for x in discover(50) if x.task_id == str(args.task_id)), None)
    if not task:
        print(json.dumps({"ok": False, "error": "Task not found."}, indent=2))
        return 2
    result = execute_task(task, args.instruction)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
