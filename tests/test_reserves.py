import json
from pathlib import Path

import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.reserves import extract


def test_extracts_official_gross_reserves(tmp_path: Path):
    path = tmp_path/"source.json"
    path.write_text(json.dumps({"status":200,"results":[{"idVariable":1,"detalle":[{"fecha":"2026-01-02","valor":45000}]}]}), encoding="utf-8")
    artifact = Artifact("test", "https://example.test", path, "h", 100, "t")
    row = extract(artifact)[0]
    assert row["series_id"] == "bcra_gross_international_reserves"
    assert row["value"] == "45000.000000"
    assert row["status"] == "official_provisional"


def test_rejects_wrong_variable(tmp_path: Path):
    path = tmp_path/"source.json"
    path.write_text(json.dumps({"status":200,"results":[{"idVariable":2,"detalle":[{"fecha":"2026-01-02","valor":1}]}]}), encoding="utf-8")
    with pytest.raises(PipelineError, match="respuesta inesperada"):
        extract(Artifact("test", "https://example.test", path, "h", 100, "t"))
