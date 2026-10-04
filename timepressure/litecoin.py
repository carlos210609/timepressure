import base64
import json
import urllib.request

class LitecoinRPC:
    def __init__(self, config):
        self.config = config

    def call(self, method, params=None):
        params = params or []
        body = json.dumps({"jsonrpc":"1.0","id":"timepressure","method":method,"params":params}).encode()
        req = urllib.request.Request(self.config.ltc_rpc_url, body, {"Content-Type":"application/json"})
        if self.config.ltc_rpc_user or self.config.ltc_rpc_password:
            raw = f"{self.config.ltc_rpc_user or ''}:{self.config.ltc_rpc_password or ''}".encode()
            req.add_header("Authorization", "Basic " + base64.b64encode(raw).decode())
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read())
        if data.get("error"):
            raise RuntimeError(f"Litecoin RPC {data['error']['code']}: {data['error']['message']}")
        return data["result"]

    def balance(self):
        return self.call("getbalance")

    def new_address(self, label="timepressure"):
        return self.call("getnewaddress", [label])

    def send(self, address, amount):
        return self.call("sendtoaddress", [address, amount, "TimePressure payout"])

def usd_to_ltc(usd, rate):
    if usd < 0 or rate <= 0:
        raise ValueError("USD and LTC/USD rate must be valid.")
    return usd / rate

def unpaid_revenue(state):
    paid = {ref for p in state.payouts for ref in p.revenue_references}
    return [r for r in state.revenue if r.reference not in paid]
