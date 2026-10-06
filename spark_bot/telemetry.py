from __future__ import annotations
from dataclasses import dataclass,asdict
from time import time
@dataclass
class SkillTelemetry:
    skill_id:str; success:bool; duration_ms:float; cost:float|None=None; lesson:str|None=None; timestamp:float=0.0
class TelemetryStore:
    def __init__(self): self.events=[]
    def record(self,event):
        if not event.timestamp: event.timestamp=time()
        self.events.append(asdict(event))
    def summary(self):
        return {'runs':len(self.events),'success_rate':sum(e['success'] for e in self.events)/len(self.events) if self.events else 0.0}
