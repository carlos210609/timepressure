"""Scope-aware bug bounty opportunity management.

This module manages programs, scope and reporting workflow. It does not perform
vulnerability exploitation. Testing must be performed only under a program's
published rules and explicit authorization.
"""
from __future__ import annotations
import json,os,time,uuid
from pathlib import Path

STATES=("DISCOVERED","ELIGIBLE","RESEARCHING","FINDING","VALIDATING","REPORTING","SUBMITTED","TRIAGED","ACCEPTED","REJECTED","PAID")

class BountyStore:
    def __init__(self,data_dir): self.path=Path(data_dir)/"bug_bounty.json"; self.data=self._load()
    def _load(self):
        try:return json.loads(self.path.read_text())
        except (OSError,ValueError):return {"programs":[],"findings":[],"submissions":[],"rewards":[]}
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(self.data,indent=2))
        try:os.chmod(self.path,0o600)
        except OSError:pass

class ScopeValidator:
    def validate(self,program,target=None,automation=False):
        if not program.get("scope"): return False,"No explicit scope was recorded."
        if target and target not in program["scope"]: return False,"Target is not explicitly in recorded scope."
        if automation and not program.get("automation_allowed",False): return False,"Automation is not explicitly allowed."
        if program.get("rules_confirmed") is not True: return False,"Program rules have not been confirmed."
        return True,"eligible"

class ProgramRanker:
    def rank(self,programs):
        out=[]
        for p in programs:
            reward=float(p.get("max_reward",0)); hours=max(float(p.get("estimated_hours",1)),.25)
            prob=float(p.get("finding_probability",.05)); risk=float(p.get("risk",.25))
            score=(reward*prob*(1-risk))/hours
            out.append((score,{**p,"expected_value_per_hour":score}))
        return [x[1] for x in sorted(out,key=lambda x:x[0],reverse=True)]

class FindingManager:
    def __init__(self,store): self.store=store
    def create(self,program_id,title,asset,severity,evidence):
        f={"id":str(uuid.uuid4()),"program_id":program_id,"title":title,"asset":asset,"severity":severity,
           "evidence":list(evidence or []),"created_at":time.time(),"state":"FINDING"}
        self.store.data["findings"].append(f); self.store.save(); return f

class EvidenceManager:
    def validate(self,finding):
        return bool(finding.get("evidence")) and all(isinstance(x,str) and x for x in finding["evidence"])

class ReportGenerator:
    def generate(self,finding):
        return {"title":finding["title"],"asset":finding["asset"],"severity":finding["severity"],
                "evidence":finding["evidence"],"note":"Draft only; review program rules before submission."}

class SubmissionTracker:
    def __init__(self,store): self.store=store
    def transition(self,submission_id,state):
        if state not in STATES: raise ValueError("Invalid bounty state.")
        for s in self.store.data["submissions"]:
            if s["id"]==submission_id: s["state"]=state; s["updated_at"]=time.time(); self.store.save(); return s
        raise ValueError("Submission not found.")

class RewardTracker:
    def __init__(self,store): self.store=store
    def record(self,submission_id,amount,reference):
        if float(amount)<=0 or not reference: raise ValueError("Verified reward requires amount and reference.")
        r={"id":str(uuid.uuid4()),"submission_id":submission_id,"amount":float(amount),
           "reference":str(reference),"timestamp":time.time(),"status":"verified"}
        self.store.data["rewards"].append(r); self.store.save(); return r

class BountyScanner:
    def __init__(self,store): self.store=store
    def discover_from_bugcrowd(self,limit=25):
        token=os.getenv("TIMPRESSURE_BUGCROWD_TOKEN") or os.getenv("TIMEPRESSURE_BUGCROWD_TOKEN")
        if not token: return {"configured":False,"programs":[],"reason":"TIMEPRESSURE_BUGCROWD_TOKEN not configured."}
        import urllib.request
        req=urllib.request.Request("https://api.bugcrowd.com/programs?fields[program]=name,code",headers={"Accept":"application/vnd.bugcrowd+json","Authorization":"Token "+token})
        with urllib.request.urlopen(req,timeout=20) as r:data=json.loads(r.read())
        programs=[]
        for x in data.get("data",[])[:limit]:
            a=x.get("attributes",{}); programs.append({"id":x.get("id"),"name":a.get("name"),"code":a.get("code"),
                "scope":[],"rules_confirmed":False,"automation_allowed":False,"max_reward":0,"estimated_hours":8,
                "finding_probability":.05,"risk":.25,"state":"DISCOVERED"})
        self.store.data["programs"].extend(programs); self.store.save()
        return {"configured":True,"programs":programs}
