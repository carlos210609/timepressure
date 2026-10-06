#!/usr/bin/env python3
"""CLI for selecting exactly one active TimePressure marketplace."""
from __future__ import annotations
import argparse,json
from marketplace_registry import list_marketplaces,select,status,discover_active,score_active,execute_active

def main(argv=None):
    p=argparse.ArgumentParser(description="TimePressure marketplace control")
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("list")
    use=sub.add_parser("use"); use.add_argument("marketplace")
    sub.add_parser("status")
    scan=sub.add_parser("scan"); scan.add_argument("--limit",type=int,default=10)
    ex=sub.add_parser("execute"); ex.add_argument("task_id"); ex.add_argument("instruction")
    a=p.parse_args(argv)
    if a.cmd=="list": print(json.dumps(list_marketplaces(),indent=2,ensure_ascii=False)); return 0
    if a.cmd=="use": print(json.dumps(select(a.marketplace),indent=2,ensure_ascii=False)); return 0
    if a.cmd=="status": print(json.dumps(status(),indent=2,ensure_ascii=False)); return 0
    if a.cmd=="scan":
        rows=[]
        for x in discover_active(a.limit):
            row=dict(vars(x)) if hasattr(x,"__dataclass_fields__") else dict(x)
            row["score"]=score_active(x); rows.append(row)
        rows.sort(key=lambda x:x["score"],reverse=True)
        print(json.dumps({"active":status()["active"],"tasks":rows},indent=2,ensure_ascii=False)); return 0
    result=execute_active(a.task_id,a.instruction); print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result.get("ok") else 2
if __name__=="__main__": raise SystemExit(main())
