"""Marketplace account/connection status for the selectable registry."""
from __future__ import annotations
from dataclasses import asdict
from marketplace_registry import list_marketplaces

def public_status() -> list[dict]:
    rows=[]
    for item in list_marketplaces():
        rows.append({
            "marketplace": item["name"],
            "auth_type": "official connector / bridge",
            "configured": item["configured"],
            "status": "active" if item["active"] and item["configured"] else ("selected" if item["active"] else "available"),
            "credential_env": item["bridge_env"],
            "note": "Secrets stay outside TimePressure source code.",
        })
    return rows

def connections():
    return public_status()

def get_credential(marketplace: str):
    key=marketplace.strip().lower().replace("-","_")
    for item in list_marketplaces():
        if item["id"]==key:
            import os
            return os.getenv(item["bridge_env"]) if item["bridge_env"] else None
    return None
