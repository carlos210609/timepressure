"""Read-only market data adapters using documented public APIs.

Coinbase Exchange public product trades and Kraken public PreTrade are used
only for market-data discovery. No order endpoints are called here.
"""
from __future__ import annotations
import json,time,urllib.parse,urllib.request,datetime

class CoinbasePublicAdapter:
    name="coinbase_exchange"
    base="https://api.exchange.coinbase.com"
    def __init__(self,products=("BTC-USD",)):
        self.products=products
    def quotes(self,asset=None):
        out=[]
        for product in self.products:
            if asset and asset.replace("/","-") not in product: continue
            url=self.base+"/products/"+urllib.parse.quote(product,safe="")+"/trades?limit=1"
            req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"TimePressure/1.0"})
            with urllib.request.urlopen(req,timeout=10) as r:data=json.loads(r.read())
            if not data: continue
            x=data[0]
            ts=_iso(x.get("time"))
            out.append({"source":self.name,"asset":product,"price":float(x["price"]),"timestamp":ts,
                        "fee":0.0,"slippage":0.0,"transfer_cost":0.0,"confidence":0.8,"risk":0.2})
        return out

class KrakenPublicAdapter:
    name="kraken"
    base="https://api.kraken.com/0/public/PreTrade"
    def __init__(self,symbols=("BTC/USD",)):
        self.symbols=symbols
    def quotes(self,asset=None):
        out=[]
        for symbol in self.symbols:
            if asset and asset.replace("-","/") not in symbol: continue
            url=self.base+"?"+urllib.parse.urlencode({"symbol":symbol})
            req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"TimePressure/1.0"})
            with urllib.request.urlopen(req,timeout=10) as r:data=json.loads(r.read())
            result=data.get("result",{})
            books=list(result.values()) if result else []
            if not books: continue
            book=books[0]
            bids=book.get("bids") or []; asks=book.get("asks") or []
            if bids:
                out.append({"source":self.name,"asset":symbol,"price":float(bids[0]["price"]),"timestamp":_iso(bids[0].get("publication_ts")),
                            "side":"bid","fee":0.0,"slippage":0.0,"transfer_cost":0.0,"confidence":0.8,"risk":0.2})
            if asks:
                out.append({"source":self.name,"asset":symbol,"price":float(asks[0]["price"]),"timestamp":_iso(asks[0].get("publication_ts")),
                            "side":"ask","fee":0.0,"slippage":0.0,"transfer_cost":0.0,"confidence":0.8,"risk":0.2})
        return out

def _iso(value):
    if not value: return 0.0
    try:return datetime.datetime.fromisoformat(str(value).replace("Z","+00:00")).timestamp()
    except ValueError:return time.time()

def configured_adapters():
    # Product/symbol selection is explicit configuration; no credentials are needed
    # for these documented public read-only market-data endpoints.
    products=tuple(x.strip() for x in __import__("os").getenv("TIMEPRESSURE_COINBASE_PRODUCTS","BTC-USD").split(",") if x.strip())
    symbols=tuple(x.strip() for x in __import__("os").getenv("TIMEPRESSURE_KRAKEN_SYMBOLS","BTC/USD").split(",") if x.strip())
    return [CoinbasePublicAdapter(products),KrakenPublicAdapter(symbols)]
