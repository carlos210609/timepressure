import unittest
from timepressure.engine import build_plan, validate_url
from timepressure.state import State

class CoreTests(unittest.TestCase):
    def test_url_validation(self):
        self.assertEqual(validate_url("https://example.com"),"https://example.com")
        with self.assertRaises(ValueError): validate_url("http://example.com")
        with self.assertRaises(ValueError): validate_url("https://localhost")
    def test_plan_has_one_execution_focus(self):
        plan=build_plan({"title":"Example","description":"A service"},50,0)
        self.assertEqual(len(plan),3); self.assertEqual(plan[1]["action"],"execute")
    def test_state_defaults(self):
        state=State(); self.assertEqual(state.pressure,50.0); self.assertEqual(state.cycles,0)

if __name__=="__main__": unittest.main()
