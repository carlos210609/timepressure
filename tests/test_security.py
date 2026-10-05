import socket
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from timepressure.security import (
    assert_github_api_url,
    assert_https_public,
    gate_action,
    task_is_expired,
)


class SecurityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(allow_network=True, browser_enabled=True)

    def test_blocks_private_and_non_https_urls(self):
        with self.assertRaises(ValueError):
            assert_https_public("http://example.com")
        with patch("timepressure.security.socket.getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ]):
            with self.assertRaises(ValueError):
                assert_https_public("https://example.com")

    def test_github_api_is_allowlisted(self):
        with patch("timepressure.security.socket.getaddrinfo", return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("140.82.112.5", 443))
        ]):
            assert_github_api_url("https://api.github.com/search/issues?q=x")
            with self.assertRaises(ValueError):
                assert_github_api_url("https://evil.example/search")

    def test_model_cannot_authorize_shell_or_financial_actions(self):
        for action in ("shell", "wallet_payout", "wallet_send", "revenue_add"):
            with self.assertRaises(PermissionError):
                gate_action(action, self.config)

    def test_browser_fill_requires_human_approval(self):
        with self.assertRaises(PermissionError):
            gate_action("browser_fill", self.config)
        self.assertTrue(gate_action("browser_fill", self.config, approved=True))

    def test_expired_task(self):
        self.assertTrue(task_is_expired({"createdAt": 0}, now=24 * 60 * 60 + 1))
        self.assertFalse(task_is_expired({"createdAt": 100}, now=101))


if __name__ == "__main__":
    unittest.main()
