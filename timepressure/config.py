import os

from .models import Config


def _num(name, default):
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def load_config():
    domains = [
        x.strip().lower()
        for x in os.getenv("TIMEPRESSURE_BROWSER_ALLOWED_DOMAINS", "").split(",")
        if x.strip()
    ]
    return Config(
        int(_num("TIMEPRESSURE_TARGET_CENTS", 1)),
        int(_num("TIMEPRESSURE_CYCLE_MS", 3600000)),
        int(_num("TIMEPRESSURE_TICK_MS", 10000)),
        os.getenv("TIMEPRESSURE_DATA_DIR", ".data"),
        os.getenv("TIMEPRESSURE_MODEL", "gpt-5.6"),
        os.getenv("OPENAI_API_KEY") or None,
        os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        os.getenv("TIMEPRESSURE_ALLOW_NETWORK", "true").lower() != "false",
        os.getenv("TIMEPRESSURE_BROWSER_ENABLED", "true").lower() == "true",
        os.getenv("TIMEPRESSURE_BROWSER_HEADLESS", "true").lower() == "true",
        domains,
        os.getenv("LTC_RPC_URL", "http://127.0.0.1:9332/"),
        os.getenv("LTC_RPC_USER") or None,
        os.getenv("LTC_RPC_PASSWORD") or None,
        os.getenv("LTC_PAYOUT_ADDRESS") or None,
        _num("LTC_MIN_PAYOUT", 0.001),
        os.getenv("LTC_AUTO_PAYOUT", "false").lower() == "true",
        (_num("LTC_USD_RATE", 0) or None),
        os.getenv("TIMEPRESSURE_SHELL_ENABLED", "false").lower() == "true",
    )
