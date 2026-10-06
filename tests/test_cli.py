import unittest

from timepressure.cli import build_parser


class CLITests(unittest.TestCase):
    def test_parser_is_traffic_only(self):
        parser = build_parser()
        for argv in [
            ["run"], ["run", "--once"], ["run", "--web"], ["web"],
            ["status"], ["doctor"], ["reset"], ["pressure"],
            ["traffic", "status"], ["traffic", "start", "https://example.com", "100"],
            ["traffic", "link", "google"], ["social", "status"],
        ]:
            with self.subTest(argv=argv):
                self.assertIsNotNone(parser.parse_args(argv))

    def test_legacy_commands_are_not_exposed(self):
        parser = build_parser()
        for argv in [["marketplaces", "list"], ["revenue", "engine"], ["wallet", "balance"], ["arbitrage", "scan"]]:
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit):
                    parser.parse_args(argv)


if __name__ == "__main__":
    unittest.main()
