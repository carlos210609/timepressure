import unittest
from unittest.mock import patch

from okx_ai import OKXAITask, score, snapshot


class OKXAIMarketplaceTests(unittest.TestCase):
    def test_score_prefers_higher_value_per_time(self):
        fast = OKXAITask("OKX.AI", "1", "Fast", "", "https://okx.ai", 4, "general", "open", 10, 0.9, 0.1)
        slow = OKXAITask("OKX.AI", "2", "Slow", "", "https://okx.ai", 4, "general", "open", 60, 0.9, 0.1)
        self.assertGreater(score(fast), score(slow))

    def test_snapshot_has_only_okx_ai(self):
        rows = snapshot()
        self.assertEqual([row["marketplace"] for row in rows], ["OKX.AI"])

    def test_write_path_is_disabled_by_default(self):
        task = OKXAITask("OKX.AI", "1", "Task", "", "https://okx.ai", 1, "general", "open")
        with patch.dict("os.environ", {"TIMEPRESSURE_MARKETPLACE_AUTOMATION": "false"}, clear=False):
            from okx_ai import execute_task
            result = execute_task(task, "do it")
        self.assertFalse(result["ok"])
        self.assertIn("disabled", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
