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

__all__=["OpportunityScore","score_opportunity","forecast_cycle_revenue","adaptive_pressure","detect_revenue_anomaly","campaign_health","next_best_action","risk_gate","dedupe_reference","experiment_score","content_variants","utm_link","runtime_health","revenue_diversity","pressure_projection","intelligence_snapshot"]
