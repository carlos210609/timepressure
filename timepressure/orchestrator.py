"""Single orchestration surface for discovery -> decision -> execution -> verification -> learning."""
from __future__ import annotations
import time, uuid
from .control_plane import Execution, TaskStatus, SafetyPolicy, VerifiedLedger, learning_update, stable_task_key
from marketplace_hub import discover_all, score

class Orchestrator:
    def __init__(self, state, store):
        self.state, self.store = state, store
        self.safety = SafetyPolicy()
        self.ledger = VerifiedLedger()

    def discover(self, limit=12):
        tasks, errors = discover_all(limit_per_marketplace=limit)
        ranked = sorted(tasks, key=score, reverse=True)
        self.state.marketplace_tasks=[dict(vars(t), score=score(t)) for t in ranked[:100]]
        self.state.marketplace_errors=errors[:50]
        self.store.save(self.state)
        return ranked

    def select(self):
        tasks=self.discover()
        if not tasks: return None
        task=tasks[0]
        self.state.decision={
            "taskKey": stable_task_key(task.marketplace, task.task_id),
            "marketplace": task.marketplace,
            "taskId": task.task_id,
            "selectedAt": time.time(),
            "score": score(task),
        }
        self.store.save(self.state)
        return task

    def begin(self, task):
        execution=Execution(str(uuid.uuid4()),task.marketplace,task.task_id)
        execution.transition(TaskStatus.RUNNING)
        return execution

    def validate_action(self, instruction, *, irreversible=False, confirmed=False):
        return self.safety.validate({
            "instruction": instruction,
            "irreversible": irreversible,
            "confirmed": confirmed,
        })

    def learn(self, task, success, reward_cents=0, minutes=0):
        learning_update(
            self.state.learning,
            marketplace=task.marketplace,
            category=task.category,
            success=success,
            reward_cents=reward_cents,
            minutes=minutes,
        )
        self.store.save(self.state)
