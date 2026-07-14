from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from argentina_economic_data.country_risk import extract
from argentina_economic_data.inflation import Artifact, PipelineError


class CountryRiskContractTests(unittest.TestCase):
    def test_short_history_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "risk.json"
            path.write_text(json.dumps([{"fecha": "2020-01-01", "valor": 1000}]), encoding="utf-8")
            artifact = Artifact("test", "https://example.test", path, "h", 100, "t")
            with self.assertRaisesRegex(PipelineError, "cobertura insuficiente"):
                extract(artifact)


if __name__ == "__main__":
    unittest.main()
