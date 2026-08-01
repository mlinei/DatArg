from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from argentina_economic_data.inflation import Artifact
from argentina_economic_data.yield_curves import (
    annual_yield, extract, extract_public_cer, extract_public_nominal,
    extract_rendimientos_cer,
)


class YieldCurveTests(unittest.TestCase):
    @staticmethod
    def artifact(path: Path, source_id: str = "fixture") -> Artifact:
        content = path.read_bytes()
        return Artifact(source_id, "https://example.test", path, hashlib.sha256(content).hexdigest(), len(content), "2026-08-01T15:00:00Z")

    def test_zero_coupon_effective_annual_yield(self):
        rate = annual_yield(80.0, date(2026, 1, 1), [(date(2027, 1, 1), 100.0)])
        self.assertAlmostEqual(rate, 0.25, places=8)

    def test_extracts_nominal_and_real_instruments(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "snapshot.csv"
            fields = [
                "snapshot_date", "ticker", "instrument_name", "curve_type", "instrument_type",
                "settlement_date", "maturity_date", "price", "cashflows", "volume", "source_url",
            ]
            rows = [
                ["2026-07-31", "S31D6", "LECAP", "nominal", "lecap", "2026-08-03", "2026-12-31", "80", "2026-12-31:100", "1000", "https://www.byma.com.ar"],
                ["2026-07-31", "TZX27", "BONCER", "cer", "boncer", "2026-08-03", "2027-06-30", "95", "2027-06-30:100", "500", "https://www.byma.com.ar"],
            ]
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerows(rows)
            result = extract(source)
        self.assertEqual([row["curve_type"] for row in result], ["cer", "nominal"])
        self.assertTrue(all(float(row["annual_yield"]) > 0 for row in result))
        self.assertEqual(result[1]["days_to_maturity"], "150")

    def test_public_nominal_merges_terms_and_delayed_quotes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            letters = root / "letters.json"
            notes = root / "notes.json"
            bonds = root / "bonds.json"
            letters.write_text(json.dumps([
                {"ticker": "S14G6", "fechaVencimiento": "2026-08-14", "vpv": 108.03},
                {"ticker": "S31G6", "fechaVencimiento": "2026-08-31", "vpv": 127.064},
                {"ticker": "T15E7", "fechaVencimiento": "2027-01-15", "vpv": 161.104},
            ]), encoding="utf-8")
            notes.write_text(json.dumps([
                {"symbol": "S14G6", "c": 107.27, "v": 10},
                {"symbol": "S31G6", "c": 124.801, "v": 20},
            ]), encoding="utf-8")
            bonds.write_text(json.dumps([{"symbol": "T15E7", "c": 144.5, "v": 30}]), encoding="utf-8")
            result = extract_public_nominal(self.artifact(letters), self.artifact(notes), self.artifact(bonds))
        self.assertEqual([row["ticker"] for row in result], ["S14G6", "S31G6", "T15E7"])
        self.assertTrue(all(row["snapshot_date"] == "2026-07-31" for row in result))
        self.assertAlmostEqual(float(result[0]["annual_yield"]), 26.39754, places=4)

    def test_empty_public_cer_is_non_fatal(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cer.json"
            source.write_text(json.dumps({
                "fechaActualizacion": "2026-07-31T23:24:31Z", "bonos": [],
                "errorExtraccion": "fuente temporalmente indisponible",
            }), encoding="utf-8")
            self.assertEqual(extract_public_cer(self.artifact(source)), [])

    def test_calculates_cer_yield_from_price_index_and_cashflows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.json"
            prices = root / "prices.json"
            cer = root / "cer.json"
            definitions = {
                ticker: {
                    "tipo": "CER", "vencimiento": maturity, "cer_emision": emission,
                    "flujos": [{"fecha": maturity, "amortizacion": 1, "tasa_interes": 0, "base": .5}],
                }
                for ticker, maturity, emission in [
                    ("TZXO6", "2026-10-30", 480), ("TZXD6", "2026-12-15", 270),
                    ("TZXM7", "2027-03-31", 360), ("TZX27", "2027-06-30", 200),
                    ("TZXD7", "2027-12-15", 270),
                ]
            }
            config.write_text(json.dumps({"bonos_cer": definitions}), encoding="utf-8")
            prices.write_text(json.dumps({"data": [
                {"symbol": ticker, "c": 100 * 800 / definition["cer_emision"] / 1.05, "v": 1000}
                for ticker, definition in definitions.items()
            ]}), encoding="utf-8")
            cer.write_text(json.dumps({"cer": 800, "fecha": "2026-07-19", "fuente": "BCRA (T-10)"}), encoding="utf-8")
            result = extract_rendimientos_cer(
                self.artifact(config), self.artifact(prices), self.artifact(cer),
            )
        self.assertEqual(len(result), 5)
        self.assertTrue(all(row["curve_type"] == "cer" for row in result))
        self.assertTrue(all(row["status"] == "calculated_from_public_price_and_cashflows" for row in result))
        self.assertGreater(float(result[0]["annual_yield"]), float(result[-1]["annual_yield"]))


if __name__ == "__main__":
    unittest.main()
