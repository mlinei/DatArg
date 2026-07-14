from __future__ import annotations

import unittest

import pandas as pd

from argentina_economic_data.emae import PipelineError, _period_rows, _sector_headers


class EmaeContractTests(unittest.TestCase):
    def test_periods_forward_fill_year(self):
        sheet = pd.DataFrame([[None, None], [2004, "Enero"], [None, "Febrero"]])
        self.assertEqual(_period_rows(sheet, 1), [(1, "2004-01"), (2, "2004-02")])

    def test_duplicate_period_fails(self):
        sheet = pd.DataFrame([[2004, "Enero"], [None, "Enero"]])
        with self.assertRaisesRegex(PipelineError, "duplicados"):
            _period_rows(sheet, 0)

    def test_sector_contract(self):
        headers = [f"{code} - sector" for code in "ABCDEFGHIJKLMNO"] + ["Impuestos netos de subsidios"]
        sheet = pd.DataFrame([[None] * 18 for _ in range(3)])
        sheet.iloc[2, 2:] = headers
        self.assertEqual(_sector_headers(sheet), list("ABCDEFGHIJKLMNO") + ["TAX"])


if __name__ == "__main__":
    unittest.main()
