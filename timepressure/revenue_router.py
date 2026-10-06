"""Routes verified revenue into the internal wallet ledger."""
from __future__ import annotations
class RevenueRouter:
    def __init__(self,wallet): self.wallet=wallet
    def route(self,source,amount,reference,metadata=None):
        return self.wallet.allocate_revenue(amount,source,reference,metadata or {})
