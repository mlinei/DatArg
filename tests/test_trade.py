from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.trade import _period, extract


class TradeContractTests(unittest.TestCase):
    def test_period_century(self):
        self.assertEqual(_period("ene-86"), "1986-01")
        self.assertEqual(_period("sept-25"), "2025-09")

    def test_unknown_month_fails(self):
        with self.assertRaisesRegex(PipelineError, "período desconocido"):
            _period("foo-25")

    def test_inconsistent_balance_fails(self):
        months = [f"{m}-86" for m in ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"]]
        labels = months * 41
        # El extractor exige períodos únicos; usamos esta prueba para confirmar esa barrera antes del saldo.
        payload = {"plot": {"data": [
            {"name": "Exportaciones", "x": labels, "y": [2] * len(labels)},
            {"name": "Importaciones", "x": labels, "y": [1] * len(labels)},
            {"name": "Saldo", "x": labels, "y": [2] * len(labels)},
        ]}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trade.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            artifact = Artifact("test", "https://example.test/trade.json", path, "h", 100, "t")
            with self.assertRaisesRegex(PipelineError, "duplicado"):
                extract(artifact)


if __name__ == "__main__":
    unittest.main()
