import json
import tempfile
import unittest
from pathlib import Path

from timepressure.oauth import OAuth


class OAuthTests(unittest.TestCase):
    def test_credentials_are_persisted_without_access_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "oauth.json"
            oauth = OAuth(path)
            data = json.loads(path.read_text())
            self.assertTrue(data["ext_agent_host_id"].startswith("urn:uuid:"))
            self.assertFalse(oauth.connected())

    def test_logout_preserves_host_identity_and_removes_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "oauth.json"
            oauth = OAuth(path)
            host_id = oauth.host_id
            path.write_text(json.dumps({
                "ext_agent_host_id": host_id,
                "access_token": "secret",
                "refresh_token": "refresh",
            }))
            oauth.logout()
            data = json.loads(path.read_text())
            self.assertEqual(data["ext_agent_host_id"], host_id)
            self.assertNotIn("access_token", data)
            self.assertNotIn("refresh_token", data)


if __name__ == "__main__":
    unittest.main()
