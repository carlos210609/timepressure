import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from timepressure.agent import Agent


class NvidiaProviderTests(unittest.TestCase):
    def test_nvidia_chat_completion_parses_content(self):
        agent = Agent.__new__(Agent)
        agent.config = SimpleNamespace(
            nvidia_api_key="test-key",
            nvidia_model="nvidia/nemotron-3-super-120b-a12b",
            nvidia_base_url="https://integrate.api.nvidia.com/v1",
        )
        body = json.dumps({
            "choices": [{"message": {"content": '{"action":"none","input":"","rationale":"ok"}'}}]
        }).encode()

        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return None
            def read(self):
                return body

        with patch("timepressure.agent.urllib.request.urlopen", return_value=Response()) as open_url:
            result = agent._ask_nvidia("test prompt")

        self.assertEqual(result, '{"action":"none","input":"","rationale":"ok"}')
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://integrate.api.nvidia.com/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")


if __name__ == "__main__":
    unittest.main()
