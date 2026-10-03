import io
import unittest
from contextlib import redirect_stdout

from timepressure.cli import build_parser


class CLITests(unittest.TestCase):
    def test_parser_supports_core_commands(self):
        parser = build_parser()
        for argv in [
            ["run"],
            ["run", "--once"],
            ["status"],
            ["status", "--watch"],
            ["doctor"],
            ["reset"],
            ["auth", "login"],
            ["auth", "logout"],
            ["auth", "status"],
            ["revenue", "add", "0.01"],
            ["wallet", "balance"],
            ["wallet", "address"],
            ["wallet", "quote", "1", "100"],
            ["browser", "open", "https://example.com"],
        ]:
            with self.subTest(argv=argv):
                self.assertIsNotNone(parser.parse_args(argv))

    def test_help_is_cli_only(self):
        parser = build_parser()
        output = io.StringIO()
        with redirect_stdout(output):
            parser.print_help()
        self.assertNotIn("tkinter", output.getvalue().lower())
        self.assertNotIn("gui", output.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
