import json
import os
import secrets
import time
from pathlib import Path

from eth_account import Account


class EVMWallet:
    """Local EVM identity wallet for Base. The signing secret stays encrypted on disk."""

    def __init__(self, data_dir):
        self.path = Path(data_dir).expanduser().resolve() / "wallet.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create(self, password=None):
        if self.path.exists():
            raise ValueError("Wallet already exists.")
        password = password or os.getenv("TIMEPRESSURE_WALLET_PASSWORD")
        if not password or len(password) < 12:
            raise ValueError("Set TIMEPRESSURE_WALLET_PASSWORD with at least 12 characters.")
        account = Account.create(secrets.token_hex(32))
        encrypted = Account.encrypt(account.key, password)
        self.path.write_text(json.dumps({
            "version": 1,
            "createdAt": time.time(),
            "address": account.address,
            "network": "base",
            "chainId": 8453,
            "keystore": encrypted,
        }, indent=2))
        try:
            self.path.chmod(0o600)
        except OSError:
            pass
        return account.address

    def address(self):
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text())["address"]

    def exists(self):
        return self.path.exists()

    def public_info(self):
        return {
            "address": self.address(),
            "network": "Base",
            "chainId": 8453,
            "keystore": str(self.path),
        }
