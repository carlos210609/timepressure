import unittest
from unittest.mock import patch

from timepressure.temp_email import is_target_domain_allowed, MailTm


class TempEmailTests(unittest.TestCase):
    def test_target_allowlist(self):
        self.assertTrue(is_target_domain_allowed("https://demo.example.com/signup", ["example.com"]))
        self.assertFalse(is_target_domain_allowed("https://evil-example.com", ["example.com"]))
        self.assertFalse(is_target_domain_allowed("http://example.com", ["example.com"]))

    def test_mailtm_create_flow(self):
        responses = [
            {"hydra:member": [{"domain": "example.mail.tm", "isActive": True}]},
            {"address": "tp123@example.mail.tm"},
            {"id": "account-id", "token": "secret-token"},
        ]
        client = MailTm()
        with patch.object(client, "_request", side_effect=responses):
            result = client.create()
        self.assertEqual(result["address"], "tp123@example.mail.tm")
        self.assertEqual(result["token"], "secret-token")

    def test_provider_host_is_pinned(self):
        with self.assertRaises(ValueError):
            MailTm("https://evil.example")


if __name__ == "__main__":
    unittest.main()
