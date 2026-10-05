import unittest
from types import SimpleNamespace
from unittest.mock import patch

from timepressure.litecoin import LitecoinRPC, _ltc_amount, usd_to_ltc


class LitecoinTests(unittest.TestCase):
    def config(self, url="http://127.0.0.1:9332/"):
        return SimpleNamespace(
            ltc_rpc_url=url,
            ltc_rpc_user=None,
            ltc_rpc_password=None,
        )

    def test_usd_to_ltc(self):
        self.assertEqual(usd_to_ltc(10, 100), 0.1)

    def test_invalid_rate(self):
        with self.assertRaises(ValueError):
            usd_to_ltc(1, 0)

    def test_negative_usd(self):
        with self.assertRaises(ValueError):
            usd_to_ltc(-1, 100)

    def test_ltc_amount_precision(self):
        self.assertEqual(str(_ltc_amount("0.12345678")), "0.12345678")
        with self.assertRaises(ValueError):
            _ltc_amount("0.123456789")

    def test_remote_http_is_blocked(self):
        with self.assertRaises(ValueError):
            LitecoinRPC(self.config("http://8.8.8.8:9332/"))

    def test_validate_address(self):
        rpc = LitecoinRPC(self.config())
        with patch.object(rpc, "call", return_value={"isvalid": True, "address": "LTC"}) as call:
            result = rpc.validate_address("LTC")
        self.assertTrue(result["isvalid"])
        call.assert_called_once_with("validateaddress", ["LTC"])

    def test_transactions_limit(self):
        rpc = LitecoinRPC(self.config())
        with self.assertRaises(ValueError):
            rpc.transactions(0)
        with self.assertRaises(ValueError):
            rpc.transactions(101)


if __name__ == "__main__":
    unittest.main()
