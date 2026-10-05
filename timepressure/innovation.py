"""Deterministic intelligence primitives for TimePressure."""
from __future__ import annotations
import statistics, time
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class OpportunityScore:
    score: float
    reasons: tuple[str, ...]

def score_opportunity(value_usd: float, effort_minutes: float, confidence: float, urgency: float = 0.5) -> OpportunityScore:
    if value_usd < 0 or effort_minutes <= 0: raise ValueError("value_usd must be >= 0 and effort_minutes > 0")
    confidence=max(0.0,min(1.0,float(confidence))); urgency=max(0.0,min(1.0,float(urgency)))
    efficiency=min(1.0,value_usd/max(1.0,effort_minutes))
    return OpportunityScore(round(100*(.50*efficiency+.35*confidence+.15*urgency),2),
                            (f"expected value \${value_usd:.2f}",f"efficiency \${value_usd/effort_minutes:.4f}/min",f"confidence {confidence:.0%}"))

def forecast_cycle_revenue(revenue_cents: Iterable[int], elapsed_seconds: float, cycle_seconds: float) -> dict:
    values=[max(0,int(x)) for x in revenue_cents]; elapsed=max(0.,float(elapsed_seconds)); cycle=max(1.,float(cycle_seconds))
    actual=sum(values); rate=actual/elapsed if elapsed else 0.; return {"actualCents":actual,"rateCentsPerHour":round(rate*3600,2),"forecastCents":round(rate*cycle)}

def adaptive_pressure(base_multiplier: float, pressure: float, progress_ratio: float) -> float:
    base=max(1.,min(3.,float(base_multiplier))); gap=max(0.,min(1.,float(pressure)/100-float(progress_ratio)))
    return round(max(1.,min(3.,base+gap*.75)),2)

def detect_revenue_anomaly(values_cents: Iterable[int], threshold: float=2.5) -> dict:
    values=[float(x) for x in values_cents]
    if len(values)<4: return {"anomaly":False,"reason":"insufficient_history"}
    mean=statistics.mean(values); stdev=statistics.pstdev(values); latest=values[-1]; z=abs(latest-mean)/stdev if stdev else 0.
    return {"anomaly":z>=max(.5,threshold),"zScore":round(z,3),"latestCents":int(latest)}

def campaign_health(verified_visits:int,target_visits:int,elapsed_seconds:float,expected_seconds:float)->dict:
    target=max(1,int(target_visits)); progress=max(0.,min(1.,verified_visits/target)); tp=max(0.,min(1.,elapsed_seconds/max(1.,expected_seconds))); delta=progress-tp
    return {"progress":round(progress*100,2),"timeProgress":round(tp*100,2),"delta":round(delta*100,2),"status":"ahead" if delta>.05 else "behind" if delta<-.05 else "on_track"}

def next_best_action(opportunities:list[dict])->dict|None:
    ranked=[]
    for item in opportunities:
        try: ranked.append((score_opportunity(float(item.get("valueUsd",0)),float(item.get("effortMinutes",1)),float(item.get("confidence",0)),float(item.get("urgency",.5))).score,item))
        except (TypeError,ValueError): continue
    if not ranked: return None
    score,item=max(ranked,key=lambda x:x[0]); return {"score":score,"action":item.get("action","review opportunity"),"source":item.get("source","unknown")}

def risk_gate(action:str,network:bool=True,financial:bool=False,external_write:bool=False)->dict:
    reasons=[]; action=action.strip()
    if not network: reasons.append("network disabled")
    if financial: reasons.append("financial action requires explicit operator approval")
    if external_write: reasons.append("external write requires authorized account and confirmation")
    allowed=bool(action) and not financial and not external_write and (network or action.startswith("local:"))
    return {"allowed":allowed,"requiresApproval":bool(financial or external_write),"reasons":reasons or ["safe local/read-only action"]}

def dedupe_reference(references:Iterable[str])->dict:
    seen=set(); duplicates=[]
    for ref in references:
        key=str(ref).strip()
        if not key: continue
        if key in seen: duplicates.append(key)
        seen.add(key)
    return {"unique":len(seen),"duplicates":duplicates}

def experiment_score(baseline:float,variant:float,sample_size:int)->dict:
    if sample_size<1: raise ValueError("sample_size must be positive")
    delta=variant-baseline; pct=delta/baseline*100 if baseline else 0.
    return {"baseline":baseline,"variant":variant,"delta":round(delta,4),"deltaPct":round(pct,2),"sampleSize":sample_size}

def content_variants(topic:str,url:str)->list[dict]:
    topic=topic.strip(); url=url.strip()
    if not topic or not url: raise ValueError("topic and url are required")
    return [{"style":"direct","text":f"Descubra {topic}. Saiba mais: {url}"},{"style":"curiosity","text":f"O que está mudando em {topic}? Veja os detalhes: {url}"},{"style":"value","text":f"Uma forma prática de entender {topic}, com mais detalhes: {url}"}]

def utm_link(url:str,source:str,campaign:str,medium:str="social")->str:
    from urllib.parse import parse_qsl,urlencode,urlsplit,urlunsplit
    parts=urlsplit(url)
    if parts.scheme not in ("http","https") or not parts.netloc: raise ValueError("url must be an absolute HTTP(S) URL")
    query=dict(parse_qsl(parts.query,keep_blank_values=True)); query.update({"utm_source":source,"utm_medium":medium,"utm_campaign":campaign})
    return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(query),parts.fragment))

def runtime_health(config,state)->dict:
    checks={"network":bool(config.allow_network),"browser":bool(config.browser_enabled),"nvidia":bool(config.nvidia_api_key),"data":state is not None,"pressure":state.pressure.status!="dead" if state else False}
    return {"healthy":all(checks.values()),"checks":checks,"timestamp":time.time()}

def revenue_diversity(revenue)->dict:
    sources={}
    for item in revenue: sources[str(item.source)]=sources.get(str(item.source),0)+int(item.cents)
    total=sum(sources.values()); shares={k:round(v/total,4) for k,v in sources.items()} if total else {}
    return {"sources":sources,"shares":shares,"sourceCount":len(sources)}

def pressure_projection(pressure:float,multiplier:float,seconds_left:float)->dict:
    p=max(0.,min(100.,float(pressure))); m=max(1.,min(3.,float(multiplier))); left=max(0.,float(seconds_left))
    return {"pressure":round(p,2),"multiplier":round(m,2),"projectedNextMinute":round(min(100.,p+(1+m*.35)*min(1.,60/max(60.,left+60))*5),2)}

def intelligence_snapshot(state,config)->dict:
    now=time.time(); p=state.pressure; elapsed=max(0.,now-p.cycle_started_at); cycle=max(1.,p.deadline-p.cycle_started_at); revenue=[x.cents for x in state.revenue[-50:]]; traffic=state.traffic
    return {"forecast":forecast_cycle_revenue(revenue,elapsed,cycle),"anomaly":detect_revenue_anomaly(revenue),"diversity":revenue_diversity(state.revenue),"health":runtime_health(config,state),"pressureProjection":pressure_projection(p.pressure,config.pressure_multiplier,max(0,p.deadline-now)),"trafficHealth":campaign_health(traffic.verified_visits,traffic.target_visits,now-traffic.started_at,cycle) if traffic else None,"dedupe":dedupe_reference([x.reference for x in state.revenue])}


# Native autonomy helpers — no external service required.

def choose_focus(goals: list[dict]) -> dict | None:
    """Choose one focus using value, urgency and effort; deterministic and local."""
    ranked=[]
    for g in goals:
        try:
            value=float(g.get("value",0)); urgency=float(g.get("urgency",0)); effort=max(1.,float(g.get("effort",1)))
            score=(max(0.,value)*.55+max(0.,min(1.,urgency))*.30*100)/(effort**.35)
            ranked.append((score,g))
        except (TypeError,ValueError):
            pass
    if not ranked: return None
    score,g=max(ranked,key=lambda x:x[0])
    return {"goal":g.get("goal","unnamed"),"score":round(score,2),"reason":"highest local value/urgency-to-effort score"}

def create_action_plan(goal: str, constraints: list[str] | None = None) -> list[dict]:
    """Create a conservative local execution plan."""
    constraints=constraints or []
    return [
        {"step":1,"action":"inspect","description":f"Inspect current state for: {goal}"},
        {"step":2,"action":"prepare","description":"Prepare the smallest reversible change"},
        {"step":3,"action":"execute","description":"Execute only approved/local-safe work"},
        {"step":4,"action":"verify","description":"Verify the result with observable evidence"},
        {"step":5,"action":"record","description":"Record outcome and next action","constraints":constraints},
    ]

def memory_relevance(query: str, memories: list[dict], limit: int = 5) -> list[dict]:
    """Lightweight keyword relevance without embeddings or an API."""
    terms={x.lower() for x in query.split() if len(x)>2}
    scored=[]
    for m in memories:
        text=f"{m.get('title','')} {m.get('content','')}".lower()
        score=sum(1 for t in terms if t in text)
        if score: scored.append((score,m))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [{"score":s,**m} for s,m in scored[:max(1,limit)]]

def budget_guard(spend_cents: int, budget_cents: int) -> dict:
    spend=max(0,int(spend_cents)); budget=max(0,int(budget_cents))
    remaining=budget-spend
    return {"spendCents":spend,"budgetCents":budget,"remainingCents":remaining,
            "status":"over_budget" if remaining<0 else "warning" if budget and remaining/budget<.15 else "ok"}

def idle_detection(last_activity: float, now: float | None = None, threshold_seconds: int = 300) -> dict:
    now=time.time() if now is None else float(now)
    idle=max(0.,now-float(last_activity))
    return {"idle":idle>=max(1,int(threshold_seconds)),"idleSeconds":round(idle,1)}

def retry_backoff(attempt: int, base_seconds: float = 1.0, max_seconds: float = 60.0) -> float:
    attempt=max(0,int(attempt))
    return round(min(max_seconds,max(0.,base_seconds)*(2**attempt)),2)

def action_fingerprint(action: str) -> str:
    import hashlib
    normalized=" ".join(str(action).lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

def safe_numeric(value, default: float = 0.0, low: float | None = None, high: float | None = None) -> float:
    try: result=float(value)
    except (TypeError,ValueError): result=float(default)
    if low is not None: result=max(low,result)
    if high is not None: result=min(high,result)
    return result

def goal_progress(completed: int, total: int) -> dict:
    total=max(1,int(total)); completed=max(0,min(total,int(completed)))
    ratio=completed/total
    return {"completed":completed,"total":total,"percent":round(ratio*100,2),"remaining":total-completed}

def decision_confidence(evidence_count: int, contradictions: int = 0) -> float:
    evidence=max(0,int(evidence_count)); contradictions=max(0,int(contradictions))
    return round(min(1.,evidence/(evidence+3.) if evidence else 0.)*(1/(1+contradictions*.35)),3)

def circuit_breaker(failures: int, threshold: int = 3) -> dict:
    failures=max(0,int(failures)); threshold=max(1,int(threshold))
    return {"open":failures>=threshold,"failures":failures,"threshold":threshold,
            "action":"pause_and_review" if failures>=threshold else "continue"}

def resource_efficiency(work_units: float, seconds: float) -> dict:
    units=max(0.,float(work_units)); seconds=max(0.,float(seconds))
    return {"units":units,"seconds":seconds,"unitsPerMinute":round(units/seconds*60,3) if seconds else 0.0}

def local_autonomy_snapshot(goals: list[dict], last_activity: float, failures: int) -> dict:
    return {
        "focus":choose_focus(goals),
        "idle":idle_detection(last_activity),
        "circuit":circuit_breaker(failures),
        "timestamp":time.time(),
    }


__all__=["OpportunityScore","score_opportunity","forecast_cycle_revenue","adaptive_pressure","detect_revenue_anomaly","campaign_health","next_best_action","risk_gate","dedupe_reference","experiment_score","content_variants","utm_link","runtime_health","revenue_diversity","pressure_projection","intelligence_snapshot"]
