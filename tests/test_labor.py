from __future__ import annotations

import unittest

import pandas as pd

from argentina_economic_data.inflation import PipelineError
from argentina_economic_data.labor import _clean, _columns


class LaborContractTests(unittest.TestCase):
    def test_label_normalization(self):
        self.assertEqual(_clean("  Gran Buenos Aires "), "gran buenos aires")

    def test_incomplete_calendar_rejected(self):
        sheet = pd.DataFrame([[None] * 3 for _ in range(5)])
        sheet.iat[2, 1] = "Año 2026"
        sheet.iat[4, 1] = "1°*"
        with self.assertRaisesRegex(PipelineError, "cobertura inesperada"):
            _columns(sheet)


if __name__ == "__main__":
    unittest.main()
