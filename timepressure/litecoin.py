import base64
import json
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation


class LitecoinRPC:
    """Small, defensive Litecoin Core JSON-RPC client.

    It talks to a local Litecoin Core node by default. Spending is never
    initiated by the agent; callers must explicitly invoke the payout CLI
    command with TIMEPRESSURE_ALLOW_PAYOUT=true.
    """

    def __init__(self, config):
        self.config = config
        self._validate_endpoint()

    def _validate_endpoint(self):
        parsed = urllib.parse.urlparse(self.config.ltc_rpc_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("LTC_RPC_URL must be a valid HTTP(S) URL.")
        if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Remote Litecoin RPC must use HTTPS.")

    def call(self, method, params=None):
        params = [] if params is None else params
        body = json.dumps({
            "jsonrpc": "1.0",
            "id": "timepressure",
            "method": method,
            "params": params,
        }).encode()
        req = urllib.request.Request(
            self.config.ltc_rpc_url,
            body,
            {"Content-Type": "application/json", "Accept": "application/json"},
        )
        if self.config.ltc_rpc_user or self.config.ltc_rpc_password:
            raw = f"{self.config.ltc_rpc_user or ''}:{self.config.ltc_rpc_password or ''}".encode()
            req.add_header("Authorization", "Basic " + base64.b64encode(raw).decode())
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read())
        except Exception as exc:
            raise RuntimeError(f"Litecoin RPC connection failed: {exc}") from exc
        if data.get("error"):
            error = data["error"]
            raise RuntimeError(f"Litecoin RPC {error.get('code')}: {error.get('message')}")
        return data.get("result")

    def balance(self):
        return float(self.call("getbalance"))

    def balances(self):
        return self.call("getbalances")

    def wallet_info(self):
        return self.call("getwalletinfo")

    def blockchain_info(self):
        return self.call("getblockchaininfo")

    def new_address(self, label="timepressure"):
        return self.call("getnewaddress", [label])

    def validate_address(self, address):
        if not isinstance(address, str) or not address.strip():
            raise ValueError("A Litecoin address is required.")
        return self.call("validateaddress", [address.strip()])

    def transactions(self, count=20):
        if not isinstance(count, int) or not 1 <= count <= 100:
            raise ValueError("Transaction count must be between 1 and 100.")
        return self.call("listtransactions", ["*", count, 0, True])

    def send(self, address, amount):
        validation = self.validate_address(address)
        if not validation.get("isvalid", False):
            raise ValueError("Invalid Litecoin address.")
        amount_dec = _ltc_amount(amount)
        return self.call(
            "sendtoaddress",
            [address.strip(), float(amount_dec), "TimePressure payout"],
        )


def _ltc_amount(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("LTC amount must be numeric.")
    if not amount.is_finite() or amount <= 0:
        raise ValueError("LTC amount must be positive.")
    # Litecoin Core supports 8 decimal places; reject accidental overprecision.
    if amount.as_tuple().exponent < -8:
        raise ValueError("LTC amount cannot have more than 8 decimal places.")
    return amount.quantize(Decimal("0.00000001"))


def usd_to_ltc(usd, rate):
    if usd < 0 or rate <= 0:
        raise ValueError("USD and LTC/USD rate must be valid.")
    return usd / rate


def unpaid_revenue(state):
    paid = {ref for p in state.payouts for ref in p.revenue_references}
    return [r for r in state.revenue if r.reference not in paid]
