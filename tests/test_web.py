import tempfile
import unittest

from timepressure.config import load_config
from timepressure.models import PressureState, State
from timepressure.web import dashboard_payload


class WebDashboardTests(unittest.TestCase):
    def test_dashboard_payload_contains_safe_runtime_data_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = State(
                1,
                0,
                PressureState(0, 10, 5, 50, "warning", 100),
                working_plan=["research a public opportunity"],
                last_thought='{"action":"fetch_url","input":"https://example.com"}',
            )
            config = load_config()
            config.data_dir = tmp
            payload = dashboard_payload(state, config)
            self.assertEqual(payload["cycleRevenueCents"], 5)
            self.assertEqual(payload["targetCents"], 10)
            self.assertIn("lastThought", payload)
            self.assertNotIn("access_token", payload)
            self.assertNotIn("refresh_token", payload)


if __name__ == "__main__":
    unittest.main()
