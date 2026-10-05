import unittest

from timepressure.intelligence import build_intelligence_report


class IntelligenceTests(unittest.TestCase):
    def test_verified_revenue_and_outcomes_influence_ranking(self):
        strategies = [
            {"id": "new", "name": "New", "category": "service", "score": 2},
            {"id": "proven", "name": "Proven", "category": "product", "score": 2},
        ]
        stats = {
            "proven": {"attempts": 4, "successes": 3, "failures": 1, "revenueUsd": 12.5}
        }
        report = build_intelligence_report(strategies, stats, limit=5)
        ranked = {row["id"]: row for row in report["rankedStrategies"]}
        self.assertGreater(ranked["proven"]["score"], ranked["new"]["score"])
        self.assertEqual(report["verifiedRevenueUsd"], 12.5)
        self.assertEqual(ranked["proven"]["verifiedRevenueUsd"], 12.5)

    def test_estimates_are_not_counted_as_revenue(self):
        report = build_intelligence_report(
            [{"id": "x", "name": "X", "category": "service", "score": 100}],
            {},
        )
        self.assertEqual(report["verifiedRevenueUsd"], 0)
        self.assertIn("never count as revenue", report["policy"])


if __name__ == "__main__":
    unittest.main()
