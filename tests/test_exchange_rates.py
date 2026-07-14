from __future__ import annotations

import unittest

from argentina_economic_data.exchange_rates import MARKETS


class ExchangeRateContractTests(unittest.TestCase):
    def test_market_mapping(self):
        self.assertEqual(MARKETS["bolsa"], "mep")
        self.assertEqual(MARKETS["contadoconliqui"], "ccl")
        self.assertEqual(len(MARKETS), 4)


if __name__ == "__main__":
    unittest.main()
