import socket
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from timepressure.security import (
    assert_agent_action,
    assert_github_api_url,
    assert_https_public_url,
    assert_path_safe,
    task_is_expired,
)


class SecurityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(
            allow_network=True,
            browser_enabled=True,
            shell_enabled=True,
        )

    def test_blocks_private_and_non_https_urls(self):
        with self.assertRaises(ValueError):
            assert_https_public_url("http://example.com")
        with patch("timepressure.security.socket.getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ]):
            with self.assertRaises(ValueError):
                assert_https_public_url("https://example.com")

    def test_github_api_is_allowlisted(self):
        with patch("timepressure.security.socket.getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("140.82.112.5", 443))
        ]):
            assert_github_api_url("https://api.github.com/search/issues?q=x")
            with self.assertRaises(ValueError):
                assert_github_api_url("https://evil.example/search")

    def test_model_cannot_use_shell_forms_or_financial_tools(self):
        for action in ("shell", "browser_click", "browser_fill", "wallet_payout", "wallet_send", "revenue_add"):
            with self.assertRaises(PermissionError):
                assert_agent_action(action, "", self.config)

    def test_browser_open_and_file_read_are_allowed(self):
        assert_agent_action("browser_open", "https://example.com", self.config)
        assert_agent_action("read_file", "README.md", self.config)

    def test_path_cannot_escape_workspace_or_read_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("timepressure.security.Path.cwd", return_value=__import__("pathlib").Path(tmp)):
                with self.assertRaises(ValueError):
                    assert_path_safe("../outside")
                with self.assertRaises(ValueError):
                    assert_path_safe(".env")

    def test_expired_task(self):
        self.assertTrue(task_is_expired({"createdAt": 0}, now=24 * 60 * 60 + 1))
        self.assertFalse(task_is_expired({"createdAt": 100}, now=101))


if __name__ == "__main__":
    unittest.main()
