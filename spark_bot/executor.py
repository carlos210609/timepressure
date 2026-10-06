from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .capabilities import Skill, get_skill
from .policy import validate_objective

@dataclass
class ExecutionResult:
    skill_id: str
    status: str
    result: dict[str, Any]
    evidence: dict[str, Any]
    verification: str

class PermissionEngine:
    def authorize(self, skill: Skill, granted: set[str]):
        missing=set(skill.permissions)-granted
        return (False,'missing_permissions:'+','.join(sorted(missing))) if missing else (True,'authorized')

class VerificationEngine:
    def verify(self, skill: Skill, result: dict[str,Any]):
        if not isinstance(result,dict) or not result.get('result'): return False,'result_missing'
        if skill.verification_method=='structured_result_and_evidence' and not result.get('evidence'): return False,'evidence_missing'
        return True,'verification_passed'

class SkillExecutor:
    def __init__(self, granted_permissions=None):
        self.permissions=PermissionEngine(); self.verifier=VerificationEngine(); self.granted_permissions=granted_permissions or {'READ'}
    def execute(self,skill_id,objective,mode='DRY_RUN',context=None):
        skill=get_skill(skill_id)
        if mode not in {'SIMULATION','DRY_RUN','PRODUCTION'}: raise ValueError('invalid execution mode')
        ok,reason=validate_objective(objective)
        if not ok: return ExecutionResult(skill_id,'blocked',{}, {'reason':reason},'policy_block')
        ok,reason=self.permissions.authorize(skill,self.granted_permissions)
        if not ok: return ExecutionResult(skill_id,'permission_denied',{}, {'reason':reason},'not_run')
        result={'result':{'skill':skill.name,'objective':objective,'mode':mode,'context_keys':sorted((context or {}).keys())},'evidence':{'mode':mode,'skill_id':skill.id}}
        verified,verification=self.verifier.verify(skill,result)
        return ExecutionResult(skill.id,'verified' if verified else 'failed',result,result['evidence'],verification)
