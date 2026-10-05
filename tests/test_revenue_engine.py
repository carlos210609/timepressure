import unittest

from timepressure.opportunity_hunter import _estimate_reward
from timepressure.task_engine import TaskPortfolio


class OpportunityHunterTests(unittest.TestCase):
    def test_estimate_reward(self):
        self.assertEqual(_estimate_reward("Bounty: $125"), 125.0)
        self.assertEqual(_estimate_reward("No amount here"), 0.0)


class TaskPortfolioTests(unittest.TestCase):
    def test_add_opportunity_and_learn(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            portfolio = TaskPortfolio(tmp)
            tasks = portfolio.add_opportunities(
                [{
                    "id": "x:1",
                    "source": "test",
                    "title": "Test bounty",
                    "url": "https://example.com",
                    "rewardUsd": 25,
                    "score": 30,
                    "instruction": "Inspect only.",
                }],
                max_active=6,
            )
            self.assertEqual(len(tasks), 1)
            portfolio.finish(tasks[0]["id"], "completed")
            self.assertEqual(portfolio.stats_snapshot()["test"]["successes"], 1)


if __name__ == "__main__":
    unittest.main()
