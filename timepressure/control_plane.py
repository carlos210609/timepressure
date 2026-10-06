"""Production control-plane primitives for TimePressure.

This module centralizes task lifecycle, safety policy, verified accounting,
health telemetry and learning without requiring third-party services.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib, time, uuid


class TaskStatus(str, Enum):
    QUEUED="queued"; RUNNING="running"; VERIFYING="verifying"
    SUBMITTED="submitted"; VERIFIED="verified"; FAILED="failed"
    CANCELLED="cancelled"; BLOCKED="blocked"


@dataclass
class Execution:
    id: str
    marketplace: str
    task_id: str
    status: str = TaskStatus.QUEUED.value
    started_at: float = 0
    finished_at: float | None = None
    attempts: int = 0
    result: dict = field(default_factory=dict)
    error: str | None = None

    def transition(self, status: TaskStatus):
        allowed={
            "queued":{"running","cancelled","blocked"},
            "running":{"verifying","failed","cancelled"},
            "verifying":{"submitted","failed"},
            "submitted":{"verified","failed"},
            "verified":set(),"failed":{"queued","cancelled"},"cancelled":set(),"blocked":{"queued","cancelled"},
        }
        if status.value not in allowed.get(self.status,set()):
            raise ValueError(f"invalid execution transition: {self.status} -> {status.value}")
        self.status=status.value
        if status == TaskStatus.RUNNING and not self.started_at:
            self.started_at=time.time()
        if status in (TaskStatus.VERIFIED,TaskStatus.FAILED,TaskStatus.CANCELLED):
            self.finished_at=time.time()


@dataclass(frozen=True)
class LedgerEntry:
    id: str
    execution_id: str
    kind: str
    cents: int
    currency: str
    reference: str
    timestamp: float


class VerifiedLedger:
    def __init__(self):
        self.entries:list[LedgerEntry]=[]
    def add_verified(self, execution_id, cents, reference, currency="USD"):
        if cents < 0: raise ValueError("verified revenue cannot be negative")
        if not reference: raise ValueError("verified revenue requires an external reference")
        entry=LedgerEntry(str(uuid.uuid4()),execution_id,"verified",int(cents),currency,reference,time.time())
        if any(x.execution_id==execution_id and x.reference==reference for x in self.entries):
            return None
        self.entries.append(entry); return entry
    def snapshot(self):
        total=sum(x.cents for x in self.entries)
        return {"verifiedRevenueCents":total,"entries":len(self.entries)}

@dataclass
class SafetyPolicy:
    require_confirmation_for_irreversible: bool=True
    allow_untrusted_instructions: bool=False
    allow_captcha_bypass: bool=False
    allow_rate_limit_evasion: bool=False
    allow_identity_impersonation: bool=False
    allow_unverified_revenue: bool=False

    def validate(self, action:dict):
        text=str(action.get("instruction","")).lower()
        forbidden=("captcha bypass","rate limit bypass","impersonate","fake identity","fabricate revenue")
        if any(x in text for x in forbidden):
            raise PermissionError("action violates TimePressure safety policy")
        if action.get("irreversible") and self.require_confirmation_for_irreversible and not action.get("confirmed"):
            raise PermissionError("explicit confirmation required for irreversible action")
        return True

def stable_task_key(marketplace, task_id):
    return hashlib.sha256(f"{marketplace}:{task_id}".encode()).hexdigest()[:24]

def health_snapshot(connectors, executions=0, failures=0):
    total=len(connectors)
    configured=sum(1 for x in connectors if x.get("configured"))
    return {
        "connectors": total, "configured": configured,
        "connectorCoverage": round(configured/total*100,1) if total else 0,
        "executions": executions, "failures": failures,
        "status": "healthy" if failures < 3 else "degraded",
    }

def learning_update(model:dict, *, marketplace, category, success, reward_cents=0, minutes=0):
    key=f"{marketplace}:{category}"
    row=model.setdefault(key,{"attempts":0,"successes":0,"rewardCents":0,"minutes":0})
    row["attempts"]+=1; row["successes"]+=1 if success else 0
    row["rewardCents"]+=max(0,int(reward_cents)); row["minutes"]+=max(0,int(minutes))
    row["successRate"]=round(row["successes"]/row["attempts"],4)
    row["avgRewardCents"]=round(row["rewardCents"]/row["attempts"],2)
    return row
