"""Secure account/connection registry for TimePressure marketplaces.

Secrets are never persisted by this module. Credentials are supplied through
environment variables or official OAuth/API-key flows exposed by adapters.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import os


@dataclass(frozen=True)
class AccountConnection:
    marketplace: str
    auth_type: str
    configured: bool
    status: str
    credential_env: str | None = None
    note: str = ""


REGISTRY = [
    ("0xWork", "official_api", "TIMEPRESSURE_0XWORK_API_URL", "Uses the marketplace's official API; account eligibility is enforced by the service."),
    ("AgentHansa", "api_key", "AGENTHANSA_API_KEY", "Authenticated agent API."),
    ("Clustly", "api_key", "CLUSTLY_API_KEY", "Official API/MCP key; account identity is managed by Clustly."),
    ("Daydreams/Lucid", "official_bridge", "TIMEPRESSURE_DAYDREAMS_BRIDGE", "Connect through an installed official bridge/SDK."),
    ("AgentPact", "wallet_signature_or_api", "AGENTPACT_API_KEY", "Official API supports owner wallet authentication and agent session keys."),
    ("BountyBook", "wallet_signature", "BOUNTYBOOK_PRIVATE_KEY", "Official API uses wallet nonce/signature authentication; do not commit private keys."),
    ("WURK", "api_key_or_mcp", "WURK_API_KEY", "Official API/MCP/x402 integrations are available; credentials stay external."),
]


def connections() -> list[AccountConnection]:
    result = []
    for marketplace, auth_type, env_name, note in REGISTRY:
        configured = bool(os.getenv(env_name))
        result.append(AccountConnection(
            marketplace=marketplace,
            auth_type=auth_type,
            configured=configured,
            status="connected" if configured else "not_configured",
            credential_env=env_name,
            note=note,
        ))
    return result


def public_status() -> list[dict]:
    # Deliberately excludes secret values.
    return [asdict(x) for x in connections()]


def get_credential(marketplace: str) -> str | None:
    for item in connections():
        if item.marketplace.lower() == marketplace.lower() and item.credential_env:
            return os.getenv(item.credential_env)
    return None
