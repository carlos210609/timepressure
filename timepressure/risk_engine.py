"""Central financial risk gate for TimePressure."""
from __future__ import annotations
import json, time
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class RiskDecision:
    decision: str
    reason: str
    risk_score: float
    checked_at: float

class RiskEngine:
    def __init__(self, data_dir: str, config=None):
        self.path = Path(data_dir) / "financial_risk.json"
        self.config = config
        self.data = self._load()

    def _load(self):
        try:
            d=json.loads(self.path.read_text())
        except (OSError,ValueError):
            d={}
        return {
            "paper_mode": bool(d.get("paper_mode", True)),
            "live_mode": bool(d.get("live_mode", False)),
            "emergency_stop": bool(d.get("emergency_stop", False)),
            "pause_all": bool(d.get("pause_all", False)),
            "limits": {
                "max_trade_amount": float(d.get("limits",{}).get("max_trade_amount", 0)),
                "max_daily_loss": float(d.get("limits",{}).get("max_daily_loss", 0)),
                "max_exposure": float(d.get("limits",{}).get("max_exposure", 0)),
                "min_profit": float(d.get("limits",{}).get("min_profit", 0.50)),
                "min_roi": float(d.get("limits",{}).get("min_roi", 0.01)),
                "max_slippage": float(d.get("limits",{}).get("max_slippage", 0.01)),
                "max_risk_score": float(d.get("limits",{}).get("max_risk_score", 0.35)),
            },
            "updated_at": float(d.get("updated_at", time.time())),
        }

    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(self.data,indent=2))
        try:
            import os; os.chmod(self.path,0o600)
        except OSError: pass

    def set_mode(self, mode):
        if mode not in ("paper","live"):
            raise ValueError("Mode must be paper or live.")
        self.data["paper_mode"]=mode=="paper"
        self.data["live_mode"]=mode=="live"
        self.save()
        return self.snapshot()

    def set_switch(self, name, enabled):
        if name not in ("emergency_stop","pause_all"):
            raise ValueError("Unknown financial switch.")
        self.data[name]=bool(enabled); self.save(); return self.snapshot()

    def set_limit(self,key,value):
        if key not in self.data["limits"]: raise ValueError("Unknown risk limit.")
        value=float(value)
        if value<0: raise ValueError("Risk limits cannot be negative.")
        self.data["limits"][key]=value; self.save(); return self.snapshot()

    def check(self, *, capital_available=0, capital_reserved=0, capital_exposure=0,
              trade_amount=0, expected_profit=0, roi=0, slippage=0, risk_score=0,
              daily_loss=0, volatility=0, confidence=1, liquidity=1, concentration=0):
        l=self.data["limits"]
        if self.data["emergency_stop"]: return RiskDecision("BLOCK","Emergency Stop is active.",1,time.time())
        if self.data["pause_all"]: return RiskDecision("BLOCK","Financial operations are paused.",1,time.time())
        if not self.data["live_mode"] and not self.data["paper_mode"]: return RiskDecision("BLOCK","No financial mode is enabled.",1,time.time())
        if trade_amount > l["max_trade_amount"] and l["max_trade_amount"] > 0: return RiskDecision("BLOCK","Trade amount exceeds limit.",risk_score,time.time())
        if l["max_daily_loss"] > 0 and daily_loss > l["max_daily_loss"]: return RiskDecision("BLOCK","Daily loss limit reached.",risk_score,time.time())
        if l["max_exposure"] > 0 and capital_exposure + trade_amount > l["max_exposure"]: return RiskDecision("BLOCK","Maximum exposure exceeded.",risk_score,time.time())
        if trade_amount > capital_available: return RiskDecision("BLOCK","Insufficient available capital.",risk_score,time.time())
        if expected_profit < l["min_profit"]: return RiskDecision("BLOCK","Expected profit is below minimum.",risk_score,time.time())
        if roi < l["min_roi"]: return RiskDecision("BLOCK","ROI is below minimum.",risk_score,time.time())
        if slippage > l["max_slippage"]: return RiskDecision("BLOCK","Slippage exceeds limit.",risk_score,time.time())
        if risk_score > l["max_risk_score"]: return RiskDecision("BLOCK","Risk score exceeds limit.",risk_score,time.time())
        if confidence < 0.5 or liquidity < 0.2: return RiskDecision("REVIEW","Confidence/liquidity requires review.",risk_score,time.time())
        if volatility > 0.5 or concentration > 0.8: return RiskDecision("REVIEW","Volatility or concentration requires review.",risk_score,time.time())
        return RiskDecision("APPROVE","All configured risk checks passed.",risk_score,time.time())

    def snapshot(self):
        return {**self.data, "mode":"LIVE" if self.data["live_mode"] else "PAPER"}

    def emergency_stop(self):
        return self.set_switch("emergency_stop", True)
