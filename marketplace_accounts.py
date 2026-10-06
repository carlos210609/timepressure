"""OKX.AI-only account/connection registry for TimePressure."""
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


def connections() -> list[AccountConnection]:
    bridge = bool(os.getenv("TIMEPRESSURE_OKX_AI_BRIDGE"))
    return [AccountConnection(
        marketplace="OKX.AI",
        auth_type="Onchain OS / official bridge",
        configured=bridge,
        status="connected" if bridge else "not_configured",
        credential_env="TIMEPRESSURE_OKX_AI_BRIDGE",
        note="Use the official OKX.AI / Onchain OS authentication flow. Secrets are never stored by TimePressure.",
    )]


def public_status() -> list[dict]:
    return [asdict(x) for x in connections()]


def get_credential(marketplace: str) -> str | None:
    if marketplace.lower() != "okx.ai":
        return None
    return os.getenv("TIMEPRESSURE_OKX_AI_BRIDGE")
