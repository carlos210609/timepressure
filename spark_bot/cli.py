from __future__ import annotations
import argparse, json
from .agent import SparkBot

def main(argv=None):
    p=argparse.ArgumentParser(prog="sparkbot",description="Spark Bot — operational super-agent")
    s=p.add_subparsers(dest="command",required=True)
    c=s.add_parser("think"); c.add_argument("objective")
    c=s.add_parser("skills"); c.add_argument("--category")
    c=s.add_parser("skill"); c.add_argument("skill_id"); c.add_argument("objective"); c.add_argument("--mode",choices=["SIMULATION","DRY_RUN","PRODUCTION"],default="DRY_RUN")
    s.add_parser("status"); s.add_parser("policy")
    c=s.add_parser("pressure"); c.add_argument("value",type=float)
    args=p.parse_args(argv); bot=SparkBot()
    if args.command=="think": out=bot.think(args.objective)
    elif args.command=="skills": out=bot.capabilities(args.category)
    elif args.command=="skill": out=bot.run_skill(args.skill_id,args.objective,args.mode)
    elif args.command=="status": out=bot.status()
    elif args.command=="policy": out=bot.policies()
    else:
        if not 0<=args.value<=100: raise SystemExit("pressure must be between 0 and 100")
        bot.pressure=args.value; out={"pressure":bot.pressure}
    print(json.dumps(out,indent=2,ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())
