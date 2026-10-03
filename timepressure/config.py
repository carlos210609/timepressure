import os
from .models import Config

def _num(name, default):
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default

def load_config():
    return Config(
        target_cents=int(_num("TIMEPRESSURE_TARGET_CENTS", 1)),
        cycle_ms=int(_num("TIMEPRESSURE_CYCLE_MS", 3600000)),
        tick_ms=int(_num("TIMEPRESSURE_TICK_MS", 10000)),
        data_dir=os.getenv("TIMEPRESSURE_DATA_DIR", ".data"),
        model=os.getenv("TIMEPRESSURE_MODEL", "gpt-5.6"),
        api_key=os.getenv("OPENAI_API_KEY") or None,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        allow_network=os.getenv("TIMEPRESSURE_ALLOW_NETWORK", "true").lower() != "false",
        ltc_rpc_url=os.getenv("LTC_RPC_URL", "http://127.0.0.1:9332/"),
        ltc_rpc_user=os.getenv("LTC_RPC_USER") or None,
        ltc_rpc_password=os.getenv("LTC_RPC_PASSWORD") or None,
        ltc_payout_address=os.getenv("LTC_PAYOUT_ADDRESS") or None,
        ltc_min_payout=_num("LTC_MIN_PAYOUT", 0.001),
        ltc_auto_payout=os.getenv("LTC_AUTO_PAYOUT", "false").lower() == "true",
        ltc_usd_rate=(_num("LTC_USD_RATE", 0) or None),
    )
