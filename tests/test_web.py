import tempfile
import unittest

from timepressure.config import load_config
from timepressure.models import PressureState, State
from timepressure.web import dashboard_payload


class WebDashboardTests(unittest.TestCase):
    def test_dashboard_is_traffic_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = State(
                1,
                0,
                PressureState(0, 100, 25, 50, "warning", 100),
                target_url="https://example.com",
            )
            config = load_config()
            config.data_dir = tmp
            config.target_url = "https://example.com"
            payload = dashboard_payload(state, config)
            self.assertEqual(payload["trafficEngine"]["targetUrl"], "https://example.com")
            self.assertEqual(payload["mode"], "website-traffic-only")
            self.assertIn("traffic", payload)
            self.assertNotIn("marketplaces", payload)
            self.assertNotIn("wallet", payload)
            self.assertNotIn("revenueEngine", payload)


if __name__ == "__main__":
    unittest.main()
