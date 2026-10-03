import json,time,urllib.request,uuid
from .models import MemoryEvent
from .pressure import calculate_pressure
from .tools import TOOLS,run_tool

class Agent:
    def __init__(self,config,store,state):self.config,self.store,self.state=config,store,state
    def _remember(self,kind,text,metadata=None):self.store.add_memory(self.state,MemoryEvent(str(uuid.uuid4()),kind,text,time.time(),metadata or {}))
    def _ask_model(self,prompt):
        payload=json.dumps({"model":self.config.model,"instructions":"You are a cautious autonomous agent. Return concise JSON only.","input":prompt,"store":False}).encode()
        req=urllib.request.Request(self.config.base_url.rstrip("/")+"/responses",payload,{"Content-Type":"application/json","Authorization":"Bearer "+self.config.api_key})
        with urllib.request.urlopen(req,timeout=60) as r:data=json.loads(r.read())
        if data.get("output_text"):return data["output_text"]
        return next((part["text"] for item in data.get("output",[]) for part in item.get("content",[]) if part.get("type") in ("output_text","text") and part.get("text")),"")
    def tick(self):
        self.state.pressure=calculate_pressure(time.time(),self.state.pressure);self.store.save(self.state)
        if self.state.pressure.status=="dead":return
        if not self.config.api_key:self._remember("observation","No OPENAI_API_KEY configured.");return
        p=self.state.pressure
        urgency="LOW"
        if p.status=="critical":urgency="HIGH"
        elif p.status=="warning":urgency="MEDIUM"
        prompt=(f"You are TimePressure, an autonomous economic agent. Goal: {self.state.working_goal}\n"
        f"Urgency: {urgency}; pressure={p.pressure:.1f}%; revenue=USD {p.cycle_revenue_cents/100:.2f}; target=USD {p.target_cents/100:.2f}; "
        f"seconds_left={max(0,int(p.deadline-time.time()))}.\n"
        "Prioritize actions with measurable revenue potential and low time-to-value. Research first when useful. "
        "Use the browser only on explicitly allowed domains. Never fabricate revenue, spam, impersonate, make purchases, gamble, bypass CAPTCHAs, "
        "evade platform limits, submit financial transactions, or expose secrets. Human approval is required for irreversible or financial actions.\n"
        f"Tools: {json.dumps(TOOLS)}\nReturn JSON: {{"action":"tool name or none","input":"...","rationale":"..."}}")
        try:
            text=self._ask_model(prompt);self.state.last_thought=text;self._remember("action",text,{"pressure":p.pressure,"urgency":urgency})
            plan=json.loads(text);action=plan.get("action")
            if action in TOOLS:
                out=run_tool(action,str(plan.get("input","")),self.config,self.state,self.store);self._remember("observation",f"{action}: {out}")
        except Exception as exc:self._remember("error",str(exc))
