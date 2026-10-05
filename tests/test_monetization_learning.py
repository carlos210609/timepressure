import unittest

from timepressure.learning import observe, strategy_multiplier, rerank
from timepressure.revenue import new_opportunity, rank_opportunities


class MonetizationLearningTests(unittest.TestCase):
    def test_revenue_rank_is_one_hour_by_default(self):
        fast = new_opportunity("test", "fast", minutes=30, revenue_cents=5000, probability=0.5)
        slow = new_opportunity("test", "slow", minutes=120, revenue_cents=50000, probability=0.9)
        self.assertEqual(rank_opportunities([fast, slow])[0].title, "fast")

    def test_learning_updates_after_outcome(self):
        learning = {}
        before = strategy_multiplier(learning, "website_audit")
        observe(learning, "website_audit", True)
        after = strategy_multiplier(learning, "website_audit")
        self.assertGreater(after, before)

    def test_learning_changes_ranking(self):
        learning = {}
        observe(learning, "a", True)
        observe(learning, "a", True)
        candidates = [{"id": "a", "score": 10}, {"id": "b", "score": 10}]
        ranked = rerank(candidates, learning)
        self.assertEqual(ranked[0]["id"], "a")


if __name__ == "__main__":
    unittest.main()
