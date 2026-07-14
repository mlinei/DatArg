from __future__ import annotations

import unittest

from argentina_economic_data.industry import DIVISIONS, _code


class IndustryContractTests(unittest.TestCase):
    def test_division_contract(self):
        self.assertEqual(len(DIVISIONS), 17)
        self.assertEqual(DIVISIONS["Nivel general"], "total")

    def test_excel_numeric_code(self):
        self.assertEqual(_code(15.0), "15")
        self.assertEqual(_code("18-19"), "18-19")


if __name__ == "__main__":
    unittest.main()
