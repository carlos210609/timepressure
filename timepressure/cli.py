from __future__ import annotations
import argparse
import json
from .engine import build_plan, fetch_site, validate_url
from .nvidia import suggest
from .state import DEFAULT_STATE, State

def parser():
    p=argparse.ArgumentParser(prog="timepressure",description="Legitimate website traffic growth CLI")
    s=p.add_subparsers(dest="command",required=True)
    for name in ("start","analyze"):
        c=s.add_parser(name); c.add_argument("--url",help="target HTTPS website")
    s.add_parser("plan"); s.add_parser("status")
    c=s.add_parser("pressure"); c.add_argument("value",type=float)
    s.add_parser("reset")
    return p

def resolve_url(state,supplied):
    url=supplied or state.target_url
    if not url: raise SystemExit("Configure a target: python3 timepressure.py start --url https://example.com")
    return validate_url(url)

def main(argv=None):
    args=parser().parse_args(argv); state=State.load()
    if args.command=="reset":
        if DEFAULT_STATE.exists(): DEFAULT_STATE.unlink()
        print("TimePressure reset."); return 0
    if args.command=="pressure":
        if not 0<=args.value<=100: raise SystemExit("pressure must be between 0 and 100")
        state.pressure=args.value; state.save(); print(f"Pressure: {state.pressure:.0f}/100"); return 0
    if args.command=="status": print(json.dumps(state.__dict__,indent=2)); return 0
    url=resolve_url(state,getattr(args,"url",None)); state.target_url=url
    if args.command=="plan":
        facts={"title":state.last_title,"description":""}
        print(json.dumps(build_plan(facts,state.pressure,state.cycles),indent=2)); return 0
    facts=fetch_site(url)
    if args.command=="analyze":
        print(json.dumps(facts,indent=2,ensure_ascii=False)); state.last_title=facts["title"]; state.save(); return 0
    plan=build_plan(facts,state.pressure,state.cycles); state.cycles+=1; state.last_action=plan[1]["tactic"]; state.last_title=facts["title"]
    print(f"Target: {url}\nSite: {facts['title'] or '(no title)'}\nPressure: {state.pressure:.0f}/100\nPlan:")
    for item in plan: print(f"  {item['priority']}. {item['action']}: {item.get('tactic',item['reason'])}")
    ai=suggest({"url":url,"facts":facts,"pressure":state.pressure,"plan":plan})
    if ai: print("\nNVIDIA suggestion:\n"+ai)
    state.save(); return 0

if __name__=="__main__": raise SystemExit(main())
