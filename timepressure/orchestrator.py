"""Unified marketplace control plane for focused execution and verified outcomes."""
from __future__ import annotations
import time
import uuid

from .control_plane import (
    Execution, TaskStatus, SafetyPolicy, VerifiedLedger,
    learning_update, stable_task_key, LedgerEntry,
)
from marketplace_hub import discover_all, score, adapters


class Orchestrator:
    def __init__(self, state, store):
        self.state, self.store = state, store
        self.safety = SafetyPolicy()
        self.ledger = VerifiedLedger()
        for raw in self.state.verified_ledger:
            try:
                self.ledger.entries.append(LedgerEntry(**raw))
            except (TypeError, ValueError):
                continue

    def _persist(self):
        self.state.verified_ledger = [vars(x) for x in self.ledger.entries[-500:]]
        self.store.save(self.state)

    def discover(self, limit=12):
        tasks, errors = discover_all(limit_per_marketplace=limit)
        ranked = sorted(tasks, key=score, reverse=True)
        self.state.marketplace_tasks = [
            dict(vars(t), score=score(t)) for t in ranked[:100]
        ]
        self.state.marketplace_errors = errors[:50]
        self.store.save(self.state)
        return ranked

    def select(self):
        tasks = self.discover()
        if not tasks:
            self.state.decision = {"status": "no_task", "selectedAt": time.time()}
            self.store.save(self.state)
            return None
        task = tasks[0]
        self.state.decision = {
            "taskKey": stable_task_key(task.marketplace, task.task_id),
            "marketplace": task.marketplace,
            "taskId": task.task_id,
            "selectedAt": time.time(),
            "score": score(task),
            "status": "selected",
        }
        self.store.save(self.state)
        return task

    def begin(self, task):
        execution = Execution(str(uuid.uuid4()), task.marketplace, task.task_id)
        execution.transition(TaskStatus.RUNNING)
        self.state.executions.append(vars(execution))
        self.state.executions = self.state.executions[-200:]
        self.state.decision = {
            **self.state.decision,
            "executionId": execution.id,
            "status": "running",
        }
        self.store.save(self.state)
        return execution

    def _save_execution(self, execution):
        for i, raw in enumerate(self.state.executions):
            if raw.get("id") == execution.id:
                self.state.executions[i] = vars(execution)
                break
        else:
            self.state.executions.append(vars(execution))
        self.state.executions = self.state.executions[-200:]
        self._persist()

    def validate_action(self, instruction, *, irreversible=False, confirmed=False):
        return self.safety.validate({
            "instruction": instruction,
            "irreversible": irreversible,
            "confirmed": confirmed,
        })

    def execute(self, task, instruction, *, irreversible=False, confirmed=False):
        self.validate_action(
            instruction, irreversible=irreversible, confirmed=confirmed
        )
        execution = self.begin(task)
        adapter = next(
            (x for x in adapters() if x.name.lower() == task.marketplace.lower()),
            None,
        )
        if adapter is None:
            execution.error = "Marketplace adapter not configured"
            execution.transition(TaskStatus.FAILED)
            self._save_execution(execution)
            self.learn(task, False)
            return execution
        try:
            result = adapter.execute(task, instruction)
            execution.result = result if isinstance(result, dict) else {"result": result}
            if not execution.result.get("ok", False):
                execution.error = str(
                    execution.result.get("error", "Execution was not verified")
                )
                execution.transition(TaskStatus.FAILED)
                self._save_execution(execution)
                self.learn(task, False)
                return execution
            execution.transition(TaskStatus.VERIFYING)
            self._save_execution(execution)
            return execution
        except Exception as exc:
            execution.error = str(exc)
            execution.transition(TaskStatus.FAILED)
            self._save_execution(execution)
            self.learn(task, False)
            return execution

    def verify(self, execution_id, *, cents, reference, minutes=0):
        raw = next(
            (x for x in self.state.executions if x.get("id") == execution_id),
            None,
        )
        if raw is None:
            raise ValueError("execution not found")
        execution = Execution(**raw)
        if execution.status != TaskStatus.VERIFYING.value:
            raise ValueError(
                f"execution must be verifying, got {execution.status}"
            )
        entry = self.ledger.add_verified(execution.id, cents, reference)
        execution.transition(TaskStatus.SUBMITTED)
        execution.transition(TaskStatus.VERIFIED)
        execution.result = {
            **execution.result,
            "verificationReference": reference,
            "verifiedCents": int(cents),
        }
        self._save_execution(execution)
        task = next(
            (
                x for x in self.state.marketplace_tasks
                if x.get("marketplace") == execution.marketplace
                and x.get("task_id") == execution.task_id
            ),
            None,
        )
        if task:
            class TaskRef:
                pass
            ref = TaskRef()
            ref.marketplace = execution.marketplace
            ref.category = task.get("category", "unknown")
            self.learn(ref, True, int(cents), minutes)
        return entry

    def cancel(self, execution_id, reason="cancelled by operator"):
        raw = next(
            (x for x in self.state.executions if x.get("id") == execution_id),
            None,
        )
        if raw is None:
            raise ValueError("execution not found")
        execution = Execution(**raw)
        execution.error = reason
        execution.transition(TaskStatus.CANCELLED)
        self._save_execution(execution)
        return execution

    def learn(self, task, success, reward_cents=0, minutes=0):
        learning_update(
            self.state.learning,
            marketplace=task.marketplace,
            category=task.category,
            success=success,
            reward_cents=reward_cents,
            minutes=minutes,
        )
        self._persist()
