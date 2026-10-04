import unittest

from timepressure.models import PressureState, State
from timepressure.triggers import evaluate


class TriggerTests(unittest.TestCase):
    def make_state(self, deadline=3600):
        return State(1, 0, PressureState(0, 1, 0, 0, "alive", deadline))

    def test_warning(self):
        self.assertIn(
            "warning_pressure",
            [x.name for x in evaluate(self.make_state(), 720)],
        )

    def test_deadline(self):
        self.assertIn(
            "deadline_imminent",
            [x.name for x in evaluate(self.make_state(30), 0)],
        )

    def test_dead(self):
        state = self.make_state(0)
        state.pressure.status = "dead"
        self.assertEqual(evaluate(state, 1)[0].name, "dead")


if __name__ == "__main__":
    unittest.main()
