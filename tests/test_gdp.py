from __future__ import annotations

import unittest

import pandas as pd

from argentina_economic_data.gdp import _sa_sheet
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


if __name__ == "__main__":
    unittest.main()
