from __future__ import annotations

import unittest

import pandas as pd

from argentina_economic_data.gdp import _matrix, _sa_sheet
from argentina_economic_data.inflation import Artifact, PipelineError


class GdpContractTests(unittest.TestCase):
    def artifact(self):
        return Artifact("test", "https://example.test/gdp.xls", __import__("pathlib").Path("x"), "h", 100, "t")

    def test_sa_schema_rejected(self):
        with self.assertRaisesRegex(PipelineError, "esquema desestacionalizado"):
            _sa_sheet(pd.DataFrame([[1, 2]]), "x", "u", self.artifact())

    def test_quarter_mapping(self):
        from argentina_economic_data.gdp import QUARTERS, ROMAN_QUARTERS
        self.assertEqual(QUARTERS["4º trimestre"], 4)
        self.assertEqual(ROMAN_QUARTERS["III"], 3)

    def test_sa_private_consumption_column(self):
        sheet = pd.DataFrame([[None] * 8 for _ in range(8)])
        sheet.iat[3, 4] = "Consumo privado"
        sheet.iat[6, 0] = 2025
        sheet.iat[6, 1] = "I"
        sheet.iat[6, 4] = 123
        records, values = _sa_sheet(sheet, "private", "index", self.artifact(), "Consumo privado")
        self.assertEqual(values["2025-Q1"], 123)
        self.assertEqual(records[0]["series_id"], "private")

    def test_original_private_consumption_row(self):
        sheet = pd.DataFrame([[None] * 121 for _ in range(12)])
        sheet.iat[3, 2] = 2025
        sheet.iat[4, 2] = "1º trimestre"
        sheet.iat[11, 0] = "P3_S14_S15"
        sheet.iat[11, 1] = "Consumo privado (5)"
        sheet.iat[11, 2] = 456
        records, values = _matrix(
            sheet, "private", "index", self.artifact(), "P3_S14_S15", "Consumo privado"
        )
        self.assertEqual(values["2025-Q1"], 456)
        self.assertEqual(records[0]["series_id"], "private_quarterly")


if __name__ == "__main__":
    unittest.main()
