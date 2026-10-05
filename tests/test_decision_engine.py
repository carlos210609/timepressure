import unittest

from timepressure.decision_engine import (
    action_key,
    select_action,
    should_allow_action,
    start_or_update,
)


class DecisionEngineTests(unittest.TestCase):
    def test_select_action_returns_only_first_real_action(self):
        plan = {
            "actions": [
                {"action": "fetch_url", "input": "https://example.com", "rationale": "research"},
                {"action": "shell", "input": "echo nope", "rationale": "parallel"},
            ]
        }
        action = select_action(plan)
        self.assertEqual(action["action"], "fetch_url")

    def test_none_plan_returns_no_action(self):
        self.assertIsNone(select_action({"actions": [{"action": "none", "input": ""}]}))

    def test_exact_repeated_action_is_blocked_after_focus_window(self):
        now = 1000.0
        action = {"action": "fetch_url", "input": "https://example.com", "rationale": "verify"}
        state = start_or_update({}, action, "ok", True, now)
        state["ticks"] = 3
        allowed, reason = should_allow_action(state, action)
        self.assertFalse(allowed)
        self.assertIn("repeated", reason)

    def test_repeated_failures_force_pivot(self):
        now = 1000.0
        action = {"action": "fetch_url", "input": "https://example.com", "rationale": "verify"}
        state = start_or_update({}, action, "timeout", False, now)
        state = start_or_update(state, action, "timeout again", False, now + 1)
        allowed, reason = should_allow_action(state, action)
        self.assertFalse(allowed)
        self.assertIn("failed repeatedly", reason)

    def test_action_key_is_stable(self):
        self.assertEqual(action_key("fetch_url", "https://example.com"), action_key("fetch_url", "https://example.com"))


if __name__ == "__main__":
    unittest.main()
