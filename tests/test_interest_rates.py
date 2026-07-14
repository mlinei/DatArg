from __future__ import annotations

import unittest

from argentina_economic_data.interest_rates import VARIABLES


class InterestRateContractTests(unittest.TestCase):
    def test_official_variable_contract(self):
        self.assertEqual(VARIABLES[7][0], "bcra_badlar_private_tna")
        self.assertEqual(VARIABLES[44][0], "bcra_tamar_private_tna")
        self.assertEqual(len(VARIABLES), 4)


if __name__ == "__main__":
    unittest.main()
