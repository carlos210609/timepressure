"""Persistent multitask portfolio and lightweight strategy learning."""

import json
import time
from pathlib import Path


class TaskPortfolio:
    def __init__(self, data_dir):
        root = Path(data_dir).expanduser().resolve()
        self.path = root / "tasks.json"
        self.stats_path = root / "strategy_stats.json"
        self.tasks = self._load(self.path, [])
        self.stats = self._load(self.stats_path, {})

    @staticmethod
    def _load(path, default):
        if not path.exists():
            return default
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, type(default)) else default
        except (OSError, ValueError, TypeError):
            return default

    @staticmethod
    def _write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def save(self):
        self._write(self.path, self.tasks[-100:])
        self._write(self.stats_path, self.stats)

    def _active(self):
        return [x for x in self.tasks if x.get("status") in {"queued", "running", "awaiting_payment"}]

    def sync(self, candidates, max_active=6):
        active = self._active()
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
        return self._active()

    def add_opportunities(self, opportunities, max_active=6):
        active = self._active()
        existing = {x.get("externalId") for x in active}
        for item in opportunities:
            if len(active) >= max_active:
                break
            if item["id"] in existing:
                continue
            task = {
                "id": f"opp-{int(time.time()*1000)}-{len(self.tasks)}",
                "externalId": item["id"],
                "strategy": item["source"],
                "name": item["title"],
                "category": "opportunity",
                "instruction": item["instruction"],
                "score": item.get("score", 0),
                "url": item.get("url"),
                "rewardUsd": item.get("rewardUsd", 0),
                "status": "queued",
                "createdAt": time.time(),
                "attempts": 0,
                "lastError": None,
            }
            self.tasks.append(task)
            active.append(task)
            existing.add(item["id"])
        self.save()
        return self._active()

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
                self._learn(task, status)
                break
        self.save()

    def _learn(self, task, status):
        key = task.get("strategy", "unknown")
        row = self.stats.setdefault(key, {"attempts": 0, "successes": 0, "failures": 0, "revenueUsd": 0.0})
        row["attempts"] += 1
        if status == "completed":
            row["successes"] += 1
        elif status == "failed":
            row["failures"] += 1

    def record_revenue(self, strategy, usd):
        row = self.stats.setdefault(strategy, {"attempts": 0, "successes": 0, "failures": 0, "revenueUsd": 0.0})
        row["revenueUsd"] = round(row["revenueUsd"] + max(0.0, usd), 2)
        self.save()

    def snapshot(self):
        return self._active()

    def stats_snapshot(self):
        return self.stats.copy()
