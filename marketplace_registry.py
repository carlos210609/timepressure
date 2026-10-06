"""Selectable marketplace registry for TimePressure.

Only one marketplace is active at a time. Non-OKX connectors use an
operator-supplied bridge instead of guessed/private APIs.
"""
from __future__ import annotations
import json, os, subprocess, shlex
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from okx_ai import discover as okx_discover, execute_task as okx_execute, score as okx_score

@dataclass(frozen=True)
class MarketplaceProfile:
    id: str
    name: str
    kind: str
    bridge_env: str | None
    description: str

PROFILES=[
 MarketplaceProfile("okx_ai","OKX.AI","native","TIMEPRESSURE_OKX_AI_BRIDGE","OKX.AI Task Marketplace"),
 MarketplaceProfile("0xwork","0xWork","bridge","TIMEPRESSURE_0XWORK_BRIDGE","0xWork connector slot"),
 MarketplaceProfile("agenthansa","AgentHansa","bridge","TIMEPRESSURE_AGENTHANSA_BRIDGE","AgentHansa connector slot"),
 MarketplaceProfile("clustly","Clustly","bridge","TIMEPRESSURE_CLUSTLY_BRIDGE","Clustly connector slot"),
 MarketplaceProfile("daydreams_lucid","Daydreams/Lucid","bridge","TIMEPRESSURE_DAYDREAMS_BRIDGE","Daydreams/Lucid connector slot"),
 MarketplaceProfile("agentpact","AgentPact","bridge","TIMEPRESSURE_AGENTPACT_BRIDGE","AgentPact connector slot"),
 MarketplaceProfile("bountybook","BountyBook","bridge","TIMEPRESSURE_BOUNTYBOOK_BRIDGE","BountyBook connector slot"),
 MarketplaceProfile("wurk","WURK","bridge","TIMEPRESSURE_WURK_BRIDGE","WURK connector slot"),
 MarketplaceProfile("upwork","Upwork","bridge","TIMEPRESSURE_UPWORK_BRIDGE","Upwork connector slot"),
 MarketplaceProfile("fiverr","Fiverr","bridge","TIMEPRESSURE_FIVERR_BRIDGE","Fiverr connector slot"),
 MarketplaceProfile("freelancer","Freelancer","bridge","TIMEPRESSURE_FREELANCER_BRIDGE","Freelancer connector slot"),
 MarketplaceProfile("clickworker","Clickworker","bridge","TIMEPRESSURE_CLICKWORKER_BRIDGE","Clickworker connector slot"),
 MarketplaceProfile("toloka","Toloka","bridge","TIMEPRESSURE_TOLOKA_BRIDGE","Toloka connector slot"),
]
BY_ID={p.id:p for p in PROFILES}

def _state_file():
 raw=os.getenv("TIMEPRESSURE_MARKETPLACE_STATE_FILE","")
 return Path(raw).expanduser() if raw else Path(os.getenv("TIMEPRESSURE_DATA_DIR",".data"))/"marketplace.json"

def active_id():
 try:
  value=str(json.loads(_state_file().read_text(encoding="utf-8")).get("active","okx_ai")).strip().lower()
  return value if value in BY_ID else "okx_ai"
 except (OSError,ValueError,TypeError): return "okx_ai"

def select(marketplace_id):
 key=marketplace_id.strip().lower().replace("-","_")
 if key not in BY_ID: raise ValueError("Unknown marketplace. Use 'marketplaces list'.")
 path=_state_file(); path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps({"active":key},indent=2),encoding="utf-8")
 return status()

def profile(marketplace_id=None): return BY_ID[marketplace_id or active_id()]
def _configured(p):\n    if p.bridge_env and os.getenv(p.bridge_env):\n        return True\n    legacy = "AGENTHANSA_API_KEY" if p.id == "agenthansa" else None\n    return bool(legacy and os.getenv(legacy))

def _generic_bridge(p,action,**payload):
 command=os.getenv(p.bridge_env or "","").strip()
 if not command: return {"ok":False,"marketplace":p.name,"error":f"{p.name} connector is not configured."}
 proc=subprocess.run(shlex.split(command),input=json.dumps({"action":action,"marketplace":p.id,**payload}),text=True,capture_output=True,timeout=300,check=False)
 if proc.returncode: return {"ok":False,"marketplace":p.name,"error":proc.stderr.strip() or "Bridge failed"}
 try: return json.loads(proc.stdout or "{}")
 except json.JSONDecodeError: return {"ok":False,"marketplace":p.name,"error":"Bridge returned invalid JSON"}

def list_marketplaces():
 active=active_id()
 return [{**asdict(p),"active":p.id==active,"configured":_configured(p)} for p in PROFILES]

def status():
 p=profile()
 return {"active":asdict(p),"configured":_configured(p),"mode":"native" if p.kind=="native" else "official_bridge","marketplaces":list_marketplaces()}

def discover_active(limit=10):
 p=profile()
 if p.id=="okx_ai": return okx_discover(limit)
 data=_generic_bridge(p,"discover",limit=max(1,min(int(limit),50)))
 return data.get("tasks",[]) if isinstance(data.get("tasks",[]),list) else []

def score_active(task):
 if str(getattr(task,"marketplace","")).lower()=="okx.ai": return okx_score(task)
 if isinstance(task,dict):
  minutes=max(1,int(task.get("estimated_minutes",30) or 30)); reward=float(task.get("reward_usd",task.get("reward",0)) or 0)
  probability=max(0,min(1,float(task.get("probability",.25) or .25))); risk=max(0,min(1,float(task.get("risk",.3) or .3)))
  return round((reward*probability*(1-.65*risk))/(minutes/60),4)
 return 0.0

def execute_active(task_id,instruction):
 p=profile()
 if os.getenv("TIMEPRESSURE_MARKETPLACE_AUTOMATION","false").lower()!="true": return {"ok":False,"marketplace":p.name,"error":"Write automation is disabled."}
 if os.getenv("TIMEPRESSURE_MARKETPLACE_ELIGIBLE","false").lower()!="true": return {"ok":False,"marketplace":p.name,"error":"Operator eligibility gate is disabled."}
 if p.id=="okx_ai":
  task=next((x for x in okx_discover(50) if x.task_id==str(task_id)),None)
  if not task: return {"ok":False,"marketplace":p.name,"error":"Task not found."}
  return okx_execute(task,instruction)
 return _generic_bridge(p,"execute",task_id=str(task_id),instruction=instruction)

__all__=["MarketplaceProfile","list_marketplaces","status","select","active_id","profile","discover_active","score_active","execute_active"]
