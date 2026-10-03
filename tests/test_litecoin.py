import unittest

from timepressure.litecoin import usd_to_ltc


class LitecoinTests(unittest.TestCase):
    def test_usd_to_ltc(self):
        self.assertEqual(usd_to_ltc(10, 100), 0.1)

    def test_invalid_rate(self):
        with self.assertRaises(ValueError):
            usd_to_ltc(1, 0)

    def test_negative_usd(self):
        with self.assertRaises(ValueError):
            usd_to_ltc(-1, 100)


if __name__ == "__main__":
    unittest.main()
