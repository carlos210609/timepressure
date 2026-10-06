"""Internal financial ledger. This is not a blockchain wallet."""
from __future__ import annotations
import hashlib,json,os,time,uuid
from pathlib import Path

BUCKETS=("AVAILABLE","RESERVED","SAVINGS","TRADING","PENDING","PROFIT","LOSS")

class WalletEngine:
    def __init__(self,data_dir):
        self.path=Path(data_dir)/"wallet.json"
        self.data=self._load()

    def _load(self):
        try:d=json.loads(self.path.read_text())
        except (OSError,ValueError): d={}
        balances={k:float(d.get("balances",{}).get(k,0)) for k in BUCKETS}
        return {"asset":str(d.get("asset","USD")),"balances":balances,
                "ledger":list(d.get("ledger",[])),
                "rules":dict(d.get("rules",{"reserve_pct":70,"growth_pct":20,"experimental_pct":10,
                    "emergency_reserve":0,"minimum_balance":0,"maximum_trade_allocation":0,
                    "automatic_profit_lock":True,"withdrawal_protection":True}))}

    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(self.data,indent=2))
        try:os.chmod(self.path,0o600)
        except OSError:pass

    def total(self): return round(sum(self.data["balances"].values()),8)
    def set_rules(self,**rules):
        for k,v in rules.items():
            if k.endswith("_pct") and float(v)<0: raise ValueError("Percentages cannot be negative.")
            if k in self.data["rules"]: self.data["rules"][k]=float(v) if isinstance(v,(int,float)) else v
        p=sum(float(self.data["rules"].get(k,0)) for k in ("reserve_pct","growth_pct","experimental_pct"))
        if abs(p-100)>1e-6: raise ValueError("reserve_pct + growth_pct + experimental_pct must equal 100.")
        self.save(); return self.snapshot()

    def credit(self,bucket,amount,source,reference="",tx_type="income",metadata=None):
        if bucket not in BUCKETS: raise ValueError("Unknown wallet bucket.")
        amount=float(amount)
        if amount<=0: raise ValueError("Amount must be positive.")
        before=self.data["balances"][bucket]; after=before+amount
        self.data["balances"][bucket]=after
        self._entry(source,tx_type,amount,reference,before,after,"posted",metadata or {},bucket)
        self.save(); return after

    def debit(self,bucket,amount,source,reference="",tx_type="expense",metadata=None):
        if bucket not in BUCKETS: raise ValueError("Unknown wallet bucket.")
        amount=float(amount)
        if amount<=0: raise ValueError("Amount must be positive.")
        if bucket=="RESERVED" and self.data["rules"].get("withdrawal_protection",True):
            raise PermissionError("Protected reserve cannot be debited automatically.")
        before=self.data["balances"][bucket]
        if amount>before: raise ValueError("Insufficient bucket balance.")
        after=before-amount; self.data["balances"][bucket]=after
        self._entry(source,tx_type,-amount,reference,before,after,"posted",metadata or {},bucket)
        self.save(); return after

    def allocate_revenue(self,amount,source,reference="",metadata=None):
        amount=float(amount)
        if amount<=0: raise ValueError("Revenue must be positive.")
        r=self.data["rules"]; total=float(r["reserve_pct"]+r["growth_pct"]+r["experimental_pct"])
        if abs(total-100)>1e-6: raise ValueError("Allocation percentages must total 100.")
        parts=[("RESERVED",amount*r["reserve_pct"]/100),("SAVINGS",amount*r["growth_pct"]/100),
               ("TRADING",amount*r["experimental_pct"]/100)]
        before=self.total()
        for bucket,value in parts:
            self.data["balances"][bucket]+=value
            self._entry(source,"revenue_allocation",value,reference,
                        self.data["balances"][bucket]-value,self.data["balances"][bucket],
                        "posted",metadata or {},bucket)
        if r.get("automatic_profit_lock",True):
            self.data["balances"]["PROFIT"] += amount
            self._entry(source,"profit_lock",amount,reference,
                        self.data["balances"]["PROFIT"]-amount,self.data["balances"]["PROFIT"],
                        "posted",metadata or {},"PROFIT")
        self.save(); return {"allocated":parts,"totalBefore":before,"totalAfter":self.total()}

    def _entry(self,source,tx_type,amount,reference,before,after,status,metadata,bucket):
        previous=self.data["ledger"][-1]["hash"] if self.data["ledger"] else "GENESIS"
        body={"id":str(uuid.uuid4()),"timestamp":time.time(),"source":str(source),"type":tx_type,
              "amount":amount,"asset":self.data["asset"],"balance_before":before,"balance_after":after,
              "reference":str(reference),"status":status,"metadata":{"bucket":bucket,**metadata},"previous_hash":previous}
        body["hash"]=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
        self.data["ledger"].append(body)

    def verify_ledger(self):
        prev="GENESIS"
        for e in self.data["ledger"]:
            raw={k:e[k] for k in ("id","timestamp","source","type","amount","asset","balance_before","balance_after","reference","status","metadata","previous_hash")}
            if e.get("previous_hash")!=prev or hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()!=e.get("hash"):
                return False
            prev=e["hash"]
        return True

    def snapshot(self):
        return {"asset":self.data["asset"],"balances":dict(self.data["balances"]),
                "total":self.total(),"rules":dict(self.data["rules"]),"ledger_entries":len(self.data["ledger"]),
                "ledger_valid":self.verify_ledger()}
