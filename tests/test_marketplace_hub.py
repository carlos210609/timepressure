import os
import unittest

from marketplace_hub import MarketTask, score


class MarketplaceHubTests(unittest.TestCase):
    def test_score_prefers_higher_expected_hourly_value(self):
        a = MarketTask("a", "1", "A", "", "", 20, "code", "open", 30, 0.5, 0.1)
        b = MarketTask("b", "2", "B", "", "", 10, "code", "open", 60, 0.9, 0.1)
        self.assertGreater(score(a), score(b))

    def test_score_is_zero_for_zero_reward(self):
        a = MarketTask("a", "1", "A", "", "", 0, "code", "open", 30, 0.5, 0.1)
        self.assertEqual(score(a), 0)

    def test_model_is_serializable(self):
        a = MarketTask("a", "1", "A", "x", "https://example.com", 2, "research", "open")
        self.assertEqual(a.marketplace, "a")
