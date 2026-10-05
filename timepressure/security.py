"""Centralized runtime security policy for TimePressure."""

import ipaddress
import os
import socket
import urllib.parse
from pathlib import Path


ALLOWED_AGENT_TOOLS = frozenset({
    "shell",
    "read_file",
    "fetch_url",
    "browser_open",
    "browser_click",
    "browser_fill",
})

BLOCKED_ACTION_WORDS = (
    "send payment", "make payment", "purchase", "buy", "checkout",
    "transfer funds", "send money", "wire", "withdraw",
    "delete account", "change password", "disable security",
)


def _truthy(name, default=False):
    return os.getenv(name, str(default).lower()).lower() == "true"


def assert_public_host(host, port=443):
    if not host:
        raise ValueError("URL must include a hostname.")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve host: {host}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(f"Network access to non-public address is blocked: {address}")


def assert_https_public_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS URLs are allowed.")
    assert_public_host(parsed.hostname, parsed.port or 443)
    return parsed


def assert_agent_action(name, input_text, config):
    if name not in ALLOWED_AGENT_TOOLS:
        raise ValueError(f"Tool is not permitted by the runtime policy: {name}")
    lowered = f"{name} {input_text}".lower()
    if any(word in lowered for word in BLOCKED_ACTION_WORDS):
        raise ValueError("Action blocked by the runtime safety policy.")
    if name == "shell" and not config.shell_enabled:
        raise ValueError("Shell is disabled by the runtime safety policy.")
    if name.startswith("browser_") and not config.browser_enabled:
        raise ValueError("Browser is disabled by the runtime safety policy.")
    if name == "fetch_url" and not config.allow_network:
        raise ValueError("Network is disabled by the runtime safety policy.")


def assert_path_safe(raw):
    root = Path.cwd().resolve()
    resolved = Path(raw).expanduser().resolve()
    if root != resolved and root not in resolved.parents:
        raise ValueError("Path is outside the workspace.")
    if resolved.name == ".env" or ".env" in resolved.parts:
        raise ValueError("Access to .env is blocked.")
    return resolved


def security_snapshot(config):
    data = Path(config.data_dir).expanduser()
    return {
        "shellEnabled": bool(config.shell_enabled),
        "networkEnabled": bool(config.allow_network),
        "browserEnabled": bool(config.browser_enabled),
        "browserAllowedDomains": list(config.browser_allowed_domains),
        "agentTools": sorted(ALLOWED_AGENT_TOOLS),
        "automaticPayouts": bool(getattr(config, "ltc_auto_payout", False)),
        "payoutEnabled": _truthy("TIMEPRESSURE_ALLOW_PAYOUT", False),
        "dataDir": str(data),
    }
