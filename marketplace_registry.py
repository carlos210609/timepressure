"""Canonical list of supported marketplace integrations."""
from marketplace_accounts import public_status

SUPPORTED_MARKETPLACES = [
    "0xWork",
    "AgentHansa",
    "Clustly",
    "Daydreams/Lucid",
    "AgentPact",
    "BountyBook",
    "WURK",
]


def status():
    return public_status()
