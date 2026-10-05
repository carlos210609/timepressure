import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from timepressure.cli import build_parser
from timepressure.models import PressureState, State
from timepressure.store import Store
from timepressure.triggers import evaluate


class CLITests(unittest.TestCase):
    def test_parser_supports_core_commands(self):
        parser = build_parser()
        for argv in [
            ["run"],
            ["run", "--once"],
            ["run", "--web"],
            ["web"],
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

    def test_trigger_evaluation_uses_live_time(self):
        state = State(1, 0, PressureState(0, 1, 0, 0, "alive", 100))
        evaluate(state, 50)
        self.assertEqual(state.pressure.status, "critical")

    def test_state_storage_is_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(tmp)
            store.init(1, 3600)
            if os.name != "nt":
                self.assertEqual(os.stat(tmp).st_mode & 0o777, 0o700)
                self.assertEqual(os.stat(store.file).st_mode & 0o777, 0o600)

    def test_help_is_cli_only(self):
        parser = build_parser()
        output = io.StringIO()
        with redirect_stdout(output):
            parser.print_help()
        self.assertNotIn("tkinter", output.getvalue().lower())
        self.assertNotIn("gui", output.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
