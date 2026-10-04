import hashlib
import json
import time
from pathlib import Path

class AuditLog:
    def __init__(self,data_dir):
        self.path=Path(data_dir).expanduser().resolve()/"audit.jsonl"

    def append(self,event,**details):
        payload={"timestamp":time.time(),"event":event,"details":details}
        payload["hash"]=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(payload,ensure_ascii=False)+"\n")

    def tail(self,limit=20):
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines()[-limit:]]
