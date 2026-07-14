from __future__ import annotations

import unittest

from argentina_economic_data.inflation import PipelineError
from argentina_economic_data.poverty import _clean_label, _number, _period


class PovertyContractTests(unittest.TestCase):
    def test_period_variants(self):
        self.assertEqual(_period("2do. semestre 2016"), "2016-S2")
        self.assertEqual(_period("1er semestre 2025"), "2025-S1")
        self.assertEqual(_period("2° semestre 2025"), "2025-S2")

    def test_footnotes_removed_from_geography(self):
        self.assertEqual(_clean_label("Total 31 aglomerados urbanos (2) (3)"), "total 31 aglomerados urbanos")

    def test_percentage_validation(self):
        self.assertEqual(str(_number("8,2", "test")), "8.2")
        with self.assertRaisesRegex(PipelineError, "fuera de rango"):
            _number(101, "test")


if __name__ == "__main__":
    unittest.main()
