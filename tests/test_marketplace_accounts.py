import os
import unittest

from marketplace_accounts import public_status


class MarketplaceAccountTests(unittest.TestCase):
    def test_status_never_exposes_secret(self):
        old = os.environ.get("AGENTHANSA_API_KEY")
        try:
            os.environ["AGENTHANSA_API_KEY"] = "super-secret"
            rows = public_status()
            row = next(x for x in rows if x["marketplace"] == "AgentHansa")
            self.assertTrue(row["configured"])
            self.assertNotIn("super-secret", str(row))
        finally:
            if old is None:
                os.environ.pop("AGENTHANSA_API_KEY", None)
            else:
                os.environ["AGENTHANSA_API_KEY"] = old

    def test_registry_has_multiple_marketplaces(self):
        rows = public_status()
        self.assertGreaterEqual(len(rows), 7)
