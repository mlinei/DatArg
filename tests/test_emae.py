from __future__ import annotations

import unittest

import pandas as pd

from decimal import Decimal

from argentina_economic_data.emae import PipelineError, _period_rows, _rebase_index, _sector_headers


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

    def test_sector_index_is_rebased_to_100(self):
        self.assertEqual(_rebase_index(Decimal("150"), Decimal("120")), Decimal("125"))
        self.assertEqual(_rebase_index(Decimal("120"), Decimal("120")), Decimal("100"))

    def test_sector_index_rejects_non_positive_base(self):
        with self.assertRaisesRegex(PipelineError, "no positivo"):
            _rebase_index(Decimal("120"), Decimal("0"))


if __name__ == "__main__":
    unittest.main()
