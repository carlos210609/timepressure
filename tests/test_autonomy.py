import tempfile
import unittest

from timepressure.autonomy import AutonomyPolicy


class AutonomyPolicyTests(unittest.TestCase):
    def test_default_is_bounded_level_three(self):
        with tempfile.TemporaryDirectory() as d:
            p = AutonomyPolicy(d)
            self.assertEqual(p.level, 3)
            ok, _ = p.can_act(expected_value_usd=2, task_value_usd=5, probability=.9, risk=.1)
            self.assertTrue(ok)

    def test_level_below_three_blocks_execution(self):
        with tempfile.TemporaryDirectory() as d:
            p = AutonomyPolicy(d)
            p.set_level(2)
            ok, reason = p.can_act(expected_value_usd=10)
            self.assertFalse(ok)
            self.assertIn("approval", reason)

    def test_risk_and_probability_limits(self):
        with tempfile.TemporaryDirectory() as d:
            p = AutonomyPolicy(d)
            ok, _ = p.can_act(expected_value_usd=10, probability=.5, risk=.1)
            self.assertFalse(ok)
            ok, _ = p.can_act(expected_value_usd=10, probability=.9, risk=.8)
            self.assertFalse(ok)

    def test_daily_action_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = AutonomyPolicy(d)
            p.set_limit("max_daily_actions", 1)
            p.record_action()
            ok, reason = p.can_act(expected_value_usd=10)
            self.assertFalse(ok)
            self.assertIn("Daily action", reason)


if __name__ == "__main__":
    unittest.main()
