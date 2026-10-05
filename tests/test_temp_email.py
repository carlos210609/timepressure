import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from timepressure.temp_email import _extract_email, is_target_domain_allowed, prepare_temp_email_for_page


class TempEmailTests(unittest.TestCase):
    def test_target_allowlist(self):
        self.assertTrue(is_target_domain_allowed("https://demo.example.com/signup", ["example.com"]))
        self.assertFalse(is_target_domain_allowed("https://evil-example.com", ["example.com"]))
        self.assertFalse(is_target_domain_allowed("http://example.com", ["example.com"]))

    def test_extracts_email_from_input_value(self):
        page = Mock()
        locator = Mock()
        locator.count.return_value = 1
        locator.nth.return_value.input_value.return_value = "tp123@example.test"
        page.locator.return_value = locator
        self.assertEqual(_extract_email(page), "tp123@example.test")

    def test_provider_must_be_allowlisted(self):
        config = SimpleNamespace(
            temp_email_enabled=True,
            temp_email_target_domains=["example.com"],
            temp_email_provider_domains=["allowed-provider.example"],
            temp_email_providers=[{"name":"untrusted","url":"https://temp-mail.io/en","domain":"temp-mail.io"}],
        )
        browser = Mock()
        browser.page.url = "https://demo.example.com/signup"
        with patch("timepressure.temp_email._open_provider") as open_provider:
            open_provider.return_value = (Mock(), config.temp_email_providers[0], "tp@example.test")
            with self.assertRaises(Exception):
                prepare_temp_email_for_page(browser, config)
            open_provider.assert_called_once()


if __name__ == "__main__":
    unittest.main()
