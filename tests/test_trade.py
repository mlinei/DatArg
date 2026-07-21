from __future__ import annotations

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.trade import _derived_balance_records, _period, extract


class TradeContractTests(unittest.TestCase):
    def test_derived_balance_records(self):
        balance = {
            f"{year}-{month:02d}": Decimal(year - 2020 + month)
            for year in (2023, 2024) for month in range(1, 13)
        }
        balance["2025-01"] = Decimal("10")
        artifact = Artifact("test", "https://example.test/trade.json", Path("trade.json"), "h", 100, "t")
        rows = _derived_balance_records(balance, artifact)
        annual = {row["period"]: row["value"] for row in rows if row["series_id"] == "indec_trade_balance_annual"}
        yoy = {row["period"]: row["value"] for row in rows if row["series_id"] == "indec_trade_balance_yoy_change"}
        self.assertEqual(set(annual), {"2023", "2024"})
        self.assertEqual(annual["2023"], "114.000000")
        self.assertEqual(yoy["2024-01"], "1.000000")
        self.assertEqual(yoy["2025-01"], "5.000000")

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
