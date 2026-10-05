import hashlib
import json
import os
import time
from pathlib import Path


class AuditLog:
    def __init__(self, data_dir):
        root = Path(data_dir).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        try:
            root.chmod(0o700)
        except OSError:
            pass
        self.path = root / "audit.jsonl"
        self.path.touch(exist_ok=True)
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def append(self, event, **details):
        payload = {"timestamp": time.time(), "event": event, "details": details}
        payload["hash"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def tail(self, limit=20):
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines()[-limit:]]
