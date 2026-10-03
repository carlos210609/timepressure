import unittest
from timepressure.models import PressureState
from timepressure.pressure import calculate_pressure, record_revenue

class PressureTests(unittest.TestCase):
    def test_starts_zero(self):
        state = PressureState(0, 1, 0, 0, "alive", 1000)
        self.assertEqual(calculate_pressure(0, state).pressure, 0)

    def test_increases(self):
        state = PressureState(0, 1, 0, 0, "alive", 1000)
        self.assertGreater(calculate_pressure(500, state).pressure, 0)

    def test_dies_after_deadline(self):
        state = PressureState(0, 1, 0, 0, "alive", 1000)
        self.assertEqual(calculate_pressure(1000, state).status, "dead")

    def test_revenue_resets(self):
        state = PressureState(0, 1, 0, 0, "alive", 1000)
        new = record_revenue(state, 1, 500)
        self.assertEqual(new.status, "alive")
        self.assertEqual(new.cycle_started_at, 500)
        self.assertEqual(new.cycle_revenue_cents, 0)

if __name__ == "__main__":
    unittest.main()
