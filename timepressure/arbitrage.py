"""Arbitrage discovery, analysis and paper/live planning."""
from __future__ import annotations
import hashlib,time,uuid
from dataclasses import dataclass,asdict

@dataclass
class ArbitrageOpportunity:
    id:str; origin:str; destination:str; asset:str; buy_price:float; sell_price:float
    gross_spread:float; fees:float; slippage:float; transfer_cost:float; net_profit:float
    roi:float; confidence:float; risk_score:float; capital_required:float
    estimated_duration:float; timestamp:float; status:str="DISCOVERED"

class FeeCalculator:
    def total(self,buy_fee,sell_fee,transfer_cost,capital): return max(0,float(buy_fee)+float(sell_fee)+float(transfer_cost)/max(capital,1e-12))

class SlippageEstimator:
    def estimate(self,quoted_price,executed_price): return abs(float(executed_price)-float(quoted_price))/max(float(quoted_price),1e-12)

class ArbitrageScanner:
    def __init__(self,adapters=None): self.adapters=list(adapters or [])
    def scan(self,asset=None):
        quotes=[]
        for a in self.adapters:
            try: quotes.extend(a.quotes(asset))
            except Exception: continue
        now=time.time()
        return [q for q in quotes if now-float(q.get("timestamp",0)) <= 30]

class ArbitrageAnalyzer:
    def analyze(self,buy,sell,capital,fees=0,slippage=0,transfer_cost=0,duration_minutes=60):
        bp=float(buy["price"]); sp=float(sell["price"]); capital=float(capital)
        if bp<=0 or sp<=0 or capital<=0: raise ValueError("Prices and capital must be positive.")
        units=capital/bp; gross=(sp-bp)*units
        total_cost=float(fees)+capital*float(slippage)+float(transfer_cost)
        net=gross-total_cost; roi=net/capital
        risk=min(1.0,max(0.0,float(buy.get("risk",0))+float(sell.get("risk",0))+float(slippage)))
        confidence=max(0.0,min(1.0,float(buy.get("confidence",1))*float(sell.get("confidence",1))))
        oid=hashlib.sha256(f'{buy.get("source")}:{sell.get("source")}:{buy.get("asset")}:{round(bp,10)}:{round(sp,10)}'.encode()).hexdigest()[:24]
        return ArbitrageOpportunity(oid,str(buy["source"]),str(sell["source"]),str(buy["asset"]),bp,sp,
          sp-bp,float(fees),float(slippage),float(transfer_cost),net,roi,confidence,risk,capital,float(duration_minutes),time.time(),
          "CANDIDATE" if net>0 else "REJECTED")

class OpportunityRanker:
    def rank(self,opportunities):
        now=time.time()
        return sorted((o for o in opportunities if now-o.timestamp<=30 and o.net_profit>0),
                      key=lambda o:(o.net_profit/max(o.estimated_duration,1),o.roi,o.confidence),reverse=True)

class ExecutionPlanner:
    def __init__(self,risk_engine): self.risk=risk_engine
    def plan(self,opp,capital_available,capital_reserved=0,exposure=0,daily_loss=0):
        d=self.risk.check(capital_available=capital_available,capital_reserved=capital_reserved,
            capital_exposure=exposure,trade_amount=opp.capital_required,expected_profit=opp.net_profit,
            roi=opp.roi,slippage=opp.slippage,risk_score=opp.risk_score, daily_loss=daily_loss,
            confidence=opp.confidence,liquidity=1)
        return {"opportunity":asdict(opp),"risk":asdict(d),"mode":self.risk.snapshot()["mode"],
                "execute":d.decision=="APPROVE" and self.risk.snapshot()["mode"]=="LIVE"}

class ArbitrageEngine:
    def __init__(self,risk_engine,adapters=None): self.scanner=ArbitrageScanner(adapters); self.risk=risk_engine
    def analyze(self,asset=None,capital=0):
        raw=self.scanner.scan(asset); out=[]
        for i,buy in enumerate(raw):
            for sell in raw[i+1:]:
                if buy.get("source")==sell.get("source") or buy.get("asset")!=sell.get("asset"): continue
                if buy["price"]>=sell["price"]: buy,sell=sell,buy
                out.append(ArbitrageAnalyzer().analyze(buy,sell,capital,
                    fees=float(buy.get("fee",0))+float(sell.get("fee",0)),
                    slippage=max(float(buy.get("slippage",0)), float(sell.get("slippage",0))),
                    transfer_cost=float(buy.get("transfer_cost",0)))
        return OpportunityRanker().rank(out)
