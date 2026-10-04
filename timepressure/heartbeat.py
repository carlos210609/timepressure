import json
import time
from pathlib import Path

DEFAULT_TASKS = [
    {"name":"pressure_check","interval":30,"enabled":True},
    {"name":"wallet_check","interval":300,"enabled":True},
    {"name":"memory_compaction","interval":900,"enabled":True},
    {"name":"health_report","interval":1800,"enabled":True},
]

class Heartbeat:
    def __init__(self, data_dir):
        self.path = Path(data_dir).expanduser().resolve() / "heartbeat.json"
        self.tasks = self._load()

    def _load(self):
        if not self.path.exists():
            return {x["name"]:{**x,"lastRun":0,"runs":0} for x in DEFAULT_TASKS}
        try:
            return json.loads(self.path.read_text())
        except (OSError, ValueError):
            return {x["name"]:{**x,"lastRun":0,"runs":0} for x in DEFAULT_TASKS}

    def save(self):
        self.path.write_text(json.dumps(self.tasks, indent=2))

    def due(self, now=None):
        now = now or time.time()
        return [x for x in self.tasks.values() if x.get("enabled",True) and now-x.get("lastRun",0)>=x["interval"]]

    def mark(self, name, now=None):
        if name in self.tasks:
            self.tasks[name]["lastRun"] = now or time.time()
            self.tasks[name]["runs"] = self.tasks[name].get("runs",0)+1
            self.save()

    def add(self, name, interval):
        if interval < 5:
            raise ValueError("Heartbeat interval must be at least 5 seconds.")
        self.tasks[name]={"name":name,"interval":interval,"enabled":True,"lastRun":0,"runs":0}
        self.save()

    def status(self):
        now=time.time()
        return [{**x,"due":x.get("enabled",True) and now-x.get("lastRun",0)>=x["interval"]} for x in self.tasks.values()]
