import unittest
from decimal import Decimal

from argentina_economic_data.credit import _gdp_denominators, _period


class CreditTests(unittest.TestCase):
    def test_bcra_decimal_period(self):
        self.assertEqual(_period(2026.05), "2026-05")
        self.assertIsNone(_period(2026.13))

    def test_gdp_denominator_uses_four_quarter_average(self):
        gdp = {
            "2024-Q1": Decimal("100"),
            "2024-Q2": Decimal("120"),
            "2024-Q3": Decimal("140"),
            "2024-Q4": Decimal("160"),
        }
        denominators = _gdp_denominators(gdp)
        self.assertEqual(denominators[2024 * 4 + 3], Decimal("130"))


if __name__ == "__main__":
    unittest.main()
