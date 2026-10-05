"""Persistent multitask portfolio for the revenue engine."""

import json
import time
from pathlib import Path


class TaskPortfolio:
    def __init__(self, data_dir):
        self.path = Path(data_dir).expanduser().resolve() / "tasks.json"
        self.tasks = self._load()

    def _load(self):
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, ValueError):
            return []

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.tasks[-100:], indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def sync(self, candidates, max_active=6):
        active = [x for x in self.tasks if x.get("status") in {"queued", "running"}]
        existing = {x.get("strategy") for x in active}
        for candidate in candidates:
            if len(active) >= max_active:
                break
            if candidate["id"] in existing:
                continue
            task = {
                "id": f"tp-{int(time.time()*1000)}-{len(self.tasks)}",
                "strategy": candidate["id"],
                "name": candidate["name"],
                "category": candidate["category"],
                "instruction": candidate["actions"],
                "score": candidate["score"],
                "status": "queued",
                "createdAt": time.time(),
                "attempts": 0,
                "lastError": None,
            }
            self.tasks.append(task)
            active.append(task)
            existing.add(candidate["id"])
        self.save()
        return [x for x in self.tasks if x.get("status") in {"queued", "running"}]

    def claim(self):
        queued = [x for x in self.tasks if x.get("status") == "queued"]
        if not queued:
            return None
        task = max(queued, key=lambda x: x.get("score", 0))
        task["status"] = "running"
        task["attempts"] = task.get("attempts", 0) + 1
        task["startedAt"] = time.time()
        self.save()
        return task

    def finish(self, task_id, status="completed", error=None):
        for task in self.tasks:
            if task.get("id") == task_id:
                task["status"] = status
                task["finishedAt"] = time.time()
                task["lastError"] = error
                break
        self.save()

    def snapshot(self):
        return [x for x in self.tasks if x.get("status") in {"queued", "running"}]
