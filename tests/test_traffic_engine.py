import unittest

from timepressure.traffic_engine import build_growth_plan, extract_site_facts, make_content_brief, select_playbook_strategies\nfrom timepressure.traffic_playbook import TRAFFIC_PLAYBOOK


class TrafficEngineTests(unittest.TestCase):
    def test_playbook_contains_exactly_500_strategies(self):
        self.assertEqual(len(TRAFFIC_PLAYBOOK), 500)
        self.assertEqual(len({item["id"] for item in TRAFFIC_PLAYBOOK}), 500)
        self.assertTrue(all(item["allowed"] if "allowed" in item else True for item in TRAFFIC_PLAYBOOK))

    def test_playbook_selection_is_bounded(self):
        class Dummy:
            decision = {"playbookIds": []}
            traffic = None
        selected = select_playbook_strategies(Dummy(), {}, 75, 5)
        self.assertEqual(len(selected), 5)
        self.assertEqual(len({item["id"] for item in selected}), 5)

    def test_extracts_public_site_facts(self):
        facts = extract_site_facts(
            "<html><head><title>Example</title><meta name='description' content='A site'></head>"
            "<body><h1>Hello</h1><p>Useful text</p></body></html>"
        )
        self.assertEqual(facts["title"], "Example")
        self.assertEqual(facts["description"], "A site")
        self.assertIn("Hello", facts["headings"])

    def test_plan_is_legitimate_and_focused(self):
        plan = build_growth_plan("https://example.com", {"title": "Example"}, 50, 1)
        actions = [x["action"] for x in plan]
        self.assertIn("analyze_site", actions)
        self.assertIn("create_content_brief", actions)
        self.assertIn("queue_social_draft", actions)
        self.assertNotIn("generate_clicks", actions)
        self.assertNotIn("fake_visits", actions)

    def test_content_brief_points_to_target(self):
        brief = make_content_brief("https://example.com", {"title": "Example", "description": "Useful service"})
        self.assertIn("https://example.com", brief["cta"])


if __name__ == "__main__":
    unittest.main()
